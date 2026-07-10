from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse ,Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse 
from .models import Favorite, Listing, ListingImage

def listings_page(request):
    qs = Listing.objects.filter(
        status='active',
        # Both must be approved before a listing shows publicly:
        # 1) the listing's own rental contract (proves the room/lease is legit)
        contract_documents__document_type='rental_contract',
        contract_documents__status='approved',
        # 2) the poster's identity (proves the person renting it out is verified)
        poster__verification_documents__document_type='id_document',
        poster__verification_documents__status='approved',
    ).distinct().prefetch_related('images')

    # ── Search ────────────────────────────────────────────────────────────────
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(city__icontains=q) |
            Q(district__icontains=q) |
            Q(address__icontains=q)
        )

    # ── Filters ───────────────────────────────────────────────────────────────
    price_max = request.GET.get('price_max')
    if price_max:
        try:
            qs = qs.filter(price__lte=float(price_max))
        except ValueError:
            pass

    types_raw = request.GET.get('types', '')
    if types_raw:
        types = [t.strip() for t in types_raw.split(',') if t.strip()]
        if types:
            qs = qs.filter(listing_type__in=types)

    smoking = request.GET.get('smoking')
    if smoking == 'no_smoking':
        qs = qs.filter(no_smoking=True)
    elif smoking == 'smoking_ok':
        qs = qs.filter(no_smoking=False)

    pets = request.GET.get('pets')
    if pets == 'pets_allowed':
        qs = qs.filter(pets_allowed=True)
    elif pets == 'no_pets':
        qs = qs.filter(no_pets=True)

    gender = request.GET.get('gender')
    if gender == 'males_only':
        qs = qs.filter(males_only=True)
    elif gender == 'females_only':
        qs = qs.filter(females_only=True)

    # ── Sort ──────────────────────────────────────────────────────────────────
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'newest':
        qs = qs.order_by('-created_at')
    else:
        qs = qs.order_by('-created_at')

    # ── AI compatibility scoring (per-seeker) ───────────────────────────────────
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'lifestyle_profile', None)

    if profile is not None:
        from compatibility_app.scoring import get_or_compute_scores_bulk

        all_listings = list(qs)
        others = [l for l in all_listings if l.poster_id != request.user.id]
        scores = get_or_compute_scores_bulk(request.user, profile, others) if others else {}
        for listing in all_listings:
            if listing.poster_id == request.user.id:
                listing.compat_score = None
            else:
                score_row = scores.get(listing.pk)
                listing.compat_score = score_row.overall_score if score_row else None
                
        compat_min = request.GET.get('compat_min')
        if compat_min:
            try:
                compat_min = int(compat_min)
                all_listings = [l for l in all_listings if l.compat_score is not None and l.compat_score >= compat_min]
            except ValueError:
                pass

        paginator = Paginator(all_listings, 12)
        page = request.GET.get('page', 1)
        listings = paginator.get_page(page)
    else:
        # Anonymous or no profile yet: unchanged DB-level pagination, zero added cost.
        paginator = Paginator(qs, 12)
        page = request.GET.get('page', 1)
        listings = paginator.get_page(page)

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user, listing__in=listings.object_list)
            .values_list('listing_id', flat=True)
        )

    return render(request, 'listings_app/listings.html', {
        'listings':     listings,
        'search_query': q,
        'favorite_ids': favorite_ids,
    })


def post_room_page(request, pk=None):
    listing = None
    if pk is not None:
        listing = get_object_or_404(Listing, pk=pk, poster=request.user)

    existing_images = [
        {'id': img.pk, 'src': img.image.url, 'label': img.room_label}
        for img in listing.images.all()
    ] if listing else []

    contract_doc = None
    if listing is not None:
        contract_doc = listing.contract_documents.filter(document_type='rental_contract').first()

    return render(request, 'listings_app/post_room.html', {
        'listing': listing,
        'existing_images_json': existing_images,
        'contract_doc': contract_doc,
    })


@login_required
def create_listing(request):
    if request.method == 'GET':
        return render(request, 'listings_app/post_room.html')

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        listing = Listing.objects.create_from_post(request.POST, request.FILES, request.user)
    except ValidationError as e:
       if is_ajax:
            return JsonResponse({'success': False, 'errors': e.message_dict})
       return render(request, 'listings_app/post_room.html', {'errors': e.message_dict})

    if is_ajax:
        redirect_url = (
            reverse('listings_app:room_detail', args=[listing.pk])
            if listing.status == 'active'
            else reverse('listings_app:my_listings')
        )
        return JsonResponse({
            'success': True,
            'listing_id': listing.pk,
            'status': listing.status,
            'redirect_url': redirect_url,
        })

    if listing.status == 'active':
        return redirect('listings_app:room_detail', pk=listing.pk)
    return redirect('listings_app:my_listings')


@login_required
@require_POST
def update_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, poster=request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        listing = Listing.objects.update_from_post(
            listing, request.POST, request.FILES,
            kept_images_json=request.POST.get('kept_image_ids', '[]'),
        )
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({'success': False, 'errors': e.message_dict})
        return render(request, 'listings_app/post_room.html', {
            'errors': e.message_dict,
            'listing': listing,
            'existing_images_json': [
                {'id': img.pk, 'src': img.image.url, 'label': img.room_label}
                for img in listing.images.all()
            ],
        })
    
    if is_ajax:
        redirect_url = (
            reverse('listings_app:room_detail', args=[listing.pk])
            if listing.status == 'active'
            else reverse('listings_app:my_listings')
        )
        return JsonResponse({
            'success': True,
            'listing_id': listing.pk,
            'status': listing.status,
            'redirect_url': redirect_url,
        })
    
    if listing.status == 'active':
        return redirect('listings_app:room_detail', pk=listing.pk)
    return redirect('listings_app:my_listings')


@login_required
def my_listings(request):
    # Exclude listings with invalid prices (NULL)
    listings = (
        Listing.objects
        .filter(poster=request.user)
        .exclude(price__isnull=True)
        .prefetch_related('images', 'contract_documents')
        .annotate(
            app_count=Count('applications'),
            pending_count=Count('applications', filter=Q(applications__status='pending')),
            favorite_count=Count('favorited_by', distinct=True),
        )
        .order_by('-created_at')
    )

    # Calculate stats using database queries instead of Python iteration
    user_listings = Listing.objects.filter(poster=request.user)
    stats = {
        'total':    user_listings.count(),
        'draft':    user_listings.filter(status='draft').count(),
        'pending':  user_listings.filter(status='pending').count(),
        'active':   user_listings.filter(status='active').count(),
        'inactive': user_listings.filter(status='inactive').count(),
        'closed':   user_listings.filter(status='closed').count(),
    }
    return render(request, 'listings_app/my_listings.html', {
        'listings': listings,
        'stats': stats,
    })


@login_required
@require_POST
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, poster=request.user)
    listing.delete()
    return redirect('listings_app:my_listings')


def room_detail(request, pk):
    from applications_app.models import Application, ListingReview

    listing = get_object_or_404(Listing, pk=pk, status='active')
    is_own_listing = (
        request.user.is_authenticated and listing.poster_id == request.user.id
    )

    # A listing counts as "fully verified" only once BOTH its rental
    # contract AND its poster's identity have been approved by admin.
    is_fully_verified = listing.contract_documents.filter(
        document_type='rental_contract', status='approved'
    ).exists() and listing.poster.verification_documents.filter(
        document_type='id_document', status='approved'
    ).exists()

    # Blocks the "direct link" loophole: without this, an unverified
    # listing wouldn't show up on /listings/ (filtered there already),
    # but anyone with its direct URL could still open this page and see
    # full details. Only the poster themself is allowed to view it
    # while it's still pending/rejected — everyone else gets a 404.
    if not is_own_listing and not is_fully_verified:
        raise Http404
    
    reviews = listing.reviews.select_related('reviewer').all()
    rating_avg = reviews.aggregate(avg=Avg('rating'))['avg']

    can_review = False
    my_application = None
    is_favorited = False
    has_profile = False
    compatibility = None
    if request.user.is_authenticated:
        my_application = Application.objects.filter(listing=listing, seeker=request.user).first()
        can_review = (
            my_application is not None
            and my_application.status == Application.STATUS_ACCEPTED
            and not reviews.filter(reviewer=request.user).exists()
        )
        is_favorited = Favorite.objects.filter(user=request.user, listing=listing).exists()

        if not is_own_listing:
            from compatibility_app.scoring import get_or_compute_score

            profile = getattr(request.user, 'lifestyle_profile', None)
            has_profile = profile is not None
            compatibility = get_or_compute_score(request.user, profile, listing)

    return render(request, 'listings_app/room_detail.html', {
        'listing':        listing,
        'reviews':        reviews,
        'rating_avg':     rating_avg,
        'can_review':     can_review,
        'my_application': my_application,
        'is_own_listing': is_own_listing,
        'is_favorited':   is_favorited,
        'has_profile':    has_profile,
        'compatibility':  compatibility,
    })


@login_required
@require_POST
def toggle_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status='active')
    favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        favorite.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'favorited': created})

    next_url = request.POST.get('next') or 'listings_app:room_detail'
    if next_url == 'listings_app:room_detail':
        return redirect(next_url, pk=pk)
    return redirect(next_url)


@login_required
def favorites_page(request):
    favorites = (
        Favorite.objects
        .filter(user=request.user)
        .select_related('listing')
        .prefetch_related('listing__images')
    )
    listings = [f.listing for f in favorites if f.listing.status == 'active']
    favorite_ids = {l.id for l in listings}

    return render(request, 'listings_app/favorites.html', {
        'listings':     listings,
        'favorite_ids': favorite_ids,
    })


@login_required
@require_POST
def post_review(request, pk):
    from applications_app.models import ListingReview

    listing = get_object_or_404(Listing, pk=pk, status='active')
    try:
        ListingReview.objects.create_from_post(listing, request.user, request.POST)
        messages.success(request, 'Your review has been posted.')
    except ValidationError as e:
        for field_errors in e.message_dict.values():
            for msg in field_errors:
                messages.error(request, msg)

    return redirect('listings_app:room_detail', pk=pk)


def photo_tour(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status='active')
    images = listing.images.all()

    label_display = dict(ListingImage.ROOM_LABEL_CHOICES)
    groups = []
    for slug, name in ListingImage.ROOM_LABEL_CHOICES:
        group_images = [img for img in images if img.room_label == slug]
        if group_images:
            groups.append({'slug': slug, 'name': name, 'images': group_images})

    return render(request, 'listings_app/photo_tour.html', {
        'listing': listing,
        'groups':  groups,
        'total':   len(images),
    })
