from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from listings_app.models import Listing
from .models import Application


def _build_demo_apps():
    """
    Build demo application data from real listings in the DB.
    Falls back to static dicts if the DB is empty.
    """
    pks_wanted   = [83, 80, 79, 78]
    listings_map = {
        l.pk: l
        for l in Listing.objects.filter(pk__in=pks_wanted).prefetch_related('images').select_related('poster')
    }

    configs = [
        {
            'pk': 83, 'status': 'accepted',
            'applied_at_fmt': 'Jan 15, 2026',
            'compatibility': 87,
            'message': 'Hi! I am a software engineer looking for a quiet place to work from home. I keep shared spaces very clean and respect quiet hours.',
            'poster_name': 'Ahmed Kamal', 'poster_initials': 'AK', 'poster_phone': '201012345678',
        },
        {
            'pk': 80, 'status': 'pending',
            'applied_at_fmt': 'Jan 17, 2026',
            'compatibility': 91,
            'message': 'I am a medical student. Non-smoker, early riser, very tidy. Looking for a calm environment to study.',
            'poster_name': 'Sara Rashed', 'poster_initials': 'SR', 'poster_phone': '',
        },
        {
            'pk': 79, 'status': 'pending',
            'applied_at_fmt': 'Jan 19, 2026',
            'compatibility': 84,
            'message': 'Expat working in finance. Quiet, professional lifestyle. Looking for a central location.',
            'poster_name': 'Khalid Hassan', 'poster_initials': 'KH', 'poster_phone': '',
        },
        {
            'pk': 78, 'status': 'rejected',
            'applied_at_fmt': 'Jan 10, 2026',
            'compatibility': 55,
            'message': 'Looking for a short-term stay for 2 months while searching for a permanent flat.',
            'poster_name': 'Layla Nour', 'poster_initials': 'LN', 'poster_phone': '',
        },
    ]

    apps = []
    for cfg in configs:
        listing = listings_map.get(cfg['pk'])
        if listing is None:
            continue

        first_image = listing.images.first()
        image_url   = first_image.image.url if first_image else None

        type_labels = {
            'private_room': 'Private Room',
            'full_apartment': 'Full Apartment',
            'shared_room': 'Shared Room',
            'roommate_wanted': 'Roommate Wanted',
        }

        apps.append({
            'pk':              cfg['pk'],
            'status':          cfg['status'],
            'applied_at_fmt':  cfg['applied_at_fmt'],
            'compatibility':   cfg['compatibility'],
            'message':         cfg['message'],
            'listing': {
                'pk':             listing.pk,
                'title':          listing.title,
                'district':       listing.district,
                'city':           listing.city,
                'price':          int(listing.price),
                'listing_type':   type_labels.get(listing.listing_type, listing.listing_type),
                'image_url':      image_url,
                'poster_name':    cfg['poster_name'],
                'poster_initials': cfg['poster_initials'],
                'poster_phone':   cfg['poster_phone'],
            },
        })

    return apps


def _application_stats(user):
    apps = Application.objects.filter(seeker=user)
    return {
        'total':    apps.count(),
        'pending':  apps.filter(status=Application.STATUS_PENDING).count(),
        'accepted': apps.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': apps.filter(status=Application.STATUS_REJECTED).count(),
    }


def my_applications(request):
    if request.user.is_authenticated:
        apps     = Application.objects.filter(seeker=request.user).select_related('listing', 'listing__poster', 'agreement').prefetch_related('listing__images')
        stats    = _application_stats(request.user)
        total    = stats['total']
        pending  = stats['pending']
        accepted = stats['accepted']
        rejected = stats['rejected']
        is_demo  = False
    else:
        apps     = _build_demo_apps()
        total    = len(apps)
        pending  = sum(1 for a in apps if a['status'] == 'pending')
        accepted = sum(1 for a in apps if a['status'] == 'accepted')
        rejected = sum(1 for a in apps if a['status'] == 'rejected')
        is_demo  = True

    return render(request, 'applications_app/my_applications.html', {
        'applications': apps,
        'total':        total,
        'pending':      pending,
        'accepted':     accepted,
        'rejected':     rejected,
        'is_demo':      is_demo,
    })


@require_POST
def apply_to_listing(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    listing = get_object_or_404(Listing, pk=pk, status='active')

    if listing.poster_id == request.user.id:
        return JsonResponse({'error': 'You cannot apply to your own listing'}, status=400)

    if Application.objects.filter(listing=listing, seeker=request.user).exists():
        return JsonResponse({'error': 'You have already applied to this listing'}, status=400)

    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'A message is required'}, status=400)

    from compatibility_app.scoring import get_or_compute_score

    profile = getattr(request.user, 'lifestyle_profile', None)
    compat_row = get_or_compute_score(request.user, profile, listing)
    # Frozen at creation time, same as message/applied_at — later profile or
    # listing edits update the live CompatibilityScore cache but never this value.
    compatibility = compat_row.overall_score if compat_row else None

    application = Application.objects.create(
        listing=listing, seeker=request.user, message=message, compatibility=compatibility,
    )
    return JsonResponse({'ok': True, 'application_id': application.pk})


@require_POST
def withdraw_application(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    app = get_object_or_404(Application, pk=pk, seeker=request.user)

    if app.status != Application.STATUS_PENDING:
        return JsonResponse({'error': 'Only pending applications can be withdrawn'}, status=400)

    app.delete()
    return JsonResponse({'ok': True, 'stats': _application_stats(request.user)})


# ── Poster-facing: applicants for a listing ──────────────────────────────────

def _listing_application_stats(listing):
    apps = Application.objects.filter(listing=listing)
    return {
        'total':    apps.count(),
        'pending':  apps.filter(status=Application.STATUS_PENDING).count(),
        'accepted': apps.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': apps.filter(status=Application.STATUS_REJECTED).count(),
    }


@login_required
def listing_applicants(request, pk):
    listing = get_object_or_404(Listing, pk=pk, poster=request.user)
    apps = (
        Application.objects
        .filter(listing=listing)
        .select_related('seeker', 'agreement')
        .order_by('-applied_at')
    )
    return render(request, 'applications_app/listing_applicants.html', {
        'listing':      listing,
        'applications': apps,
        'stats':        _listing_application_stats(listing),
    })


@login_required
@require_POST
def accept_application(request, pk):
    app = get_object_or_404(Application, pk=pk, listing__poster=request.user)
    app.status = Application.STATUS_ACCEPTED
    app.poster_note = request.POST.get('poster_note', '').strip()
    app.save(update_fields=['status', 'poster_note', 'updated_at'])
    return JsonResponse({'ok': True, 'stats': _listing_application_stats(app.listing)})


@login_required
@require_POST
def reject_application(request, pk):
    app = get_object_or_404(Application, pk=pk, listing__poster=request.user)
    app.status = Application.STATUS_REJECTED
    app.poster_note = request.POST.get('poster_note', '').strip()
    app.save(update_fields=['status', 'poster_note', 'updated_at'])
    return JsonResponse({'ok': True, 'stats': _listing_application_stats(app.listing)})
