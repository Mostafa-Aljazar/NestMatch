from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Listing, ListingImage


def listings_page(request):
    qs = Listing.objects.filter(status='active').prefetch_related('images')

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

    # ── Paginate ──────────────────────────────────────────────────────────────
    paginator = Paginator(qs, 12)
    page = request.GET.get('page', 1)
    listings = paginator.get_page(page)

    return render(request, 'listings_app/listings.html', {
        'listings':     listings,
        'search_query': q,
    })


def post_room_page(request):
    return render(request, 'listings_app/post_room.html')


def create_listing(request):
    if request.method == 'GET':
        return render(request, 'listings_app/post_room.html')

    try:
        listing = Listing.objects.create_from_post(request.POST, request.FILES, request.user)
    except ValidationError as e:
        return render(request, 'listings_app/post_room.html', {
            'errors': e.message_dict,
        })

    if listing.status == 'active':
        return redirect('listings_app:room_detail', pk=listing.pk)
    return redirect('dashboard_app:index')


def room_detail(request, pk):
    from applications_app.models import Application, ListingReview

    listing = get_object_or_404(Listing, pk=pk, status='active')
    reviews = listing.reviews.select_related('reviewer').all()
    rating_avg = reviews.aggregate(avg=Avg('rating'))['avg']

    can_review = False
    my_application = None
    if request.user.is_authenticated:
        my_application = Application.objects.filter(listing=listing, seeker=request.user).first()
        can_review = (
            my_application is not None
            and my_application.status == Application.STATUS_ACCEPTED
            and not reviews.filter(reviewer=request.user).exists()
        )

    return render(request, 'listings_app/room_detail.html', {
        'listing':        listing,
        'reviews':        reviews,
        'rating_avg':     rating_avg,
        'can_review':     can_review,
        'my_application': my_application,
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
