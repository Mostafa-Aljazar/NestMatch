from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json

from accounts_app.models import User, VerificationDocument, Testimonial
from listings_app.models import Listing
from applications_app.models import Application
from core_app.models import SiteContent, ContactMessage


# ─────────────────────────────────────────────
# Admin check
# ─────────────────────────────────────────────
def is_admin(user):
    return user.is_authenticated and user.is_staff


# ─────────────────────────────────────────────
# OVERVIEW PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def overview(request):
    total_users = User.objects.count()
    active_listings = Listing.objects.filter(status='active').count()
    total_applications = Application.objects.count()
    banned_users = User.objects.filter(is_active=False).count()
    unread_messages = ContactMessage.objects.filter(is_read=False).count()

    thirty_days_ago = timezone.now() - timedelta(days=30)

    users_per_day = (
        User.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    listings_per_day = (
        Listing.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    chart_users = json.dumps([
        {'day': str(r['day']), 'count': r['count']} for r in users_per_day
    ])

    chart_listings = json.dumps([
        {'day': str(r['day']), 'count': r['count']} for r in listings_per_day
    ])

    top_cities_qs = (
        Listing.objects.filter(status='active', city__isnull=False)
        .exclude(city='')
        .values('city')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    total_active = active_listings or 1

    top_cities = [
        {
            'city': row['city'],
            'count': row['count'],
            'percent': round(row['count'] / total_active * 100),
        }
        for row in top_cities_qs
    ]

    top_listings = (
        Listing.objects.annotate(app_count=Count('applications'))
        .order_by('-app_count')[:5]
    )

    recent_users = User.objects.order_by('-created_at')[:10]

    context = {
        'current_tab': 'overview',
        'total_users': total_users,
        'active_listings': active_listings,
        'total_applications': total_applications,
        'banned_users': banned_users,
        'unread_messages': unread_messages,
        'chart_users': chart_users,
        'chart_listings': chart_listings,
        'top_cities': top_cities,
        'top_listings': top_listings,
        'recent_users': recent_users,
    }

    return render(request, 'dashboard_app/overview.html', context)


# ─────────────────────────────────────────────
# USERS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def users_list(request):
    from django.core.paginator import Paginator

    all_users = (
        User.objects.annotate(
            listing_count=Count('listings', distinct=True),
            application_count=Count('applications', distinct=True),
        )
        .order_by('-created_at')
    )

    paginator = Paginator(all_users, 10)  # 10 users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'current_tab': 'users',
        'page_obj': page_obj,
        'all_users': page_obj.object_list,
    }

    return render(request, 'dashboard_app/users.html', context)


# ─────────────────────────────────────────────
# LISTINGS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def listings_list(request):
    all_listings = (
        Listing.objects.select_related('poster')
        .annotate(app_count=Count('applications'))
        .order_by('-created_at')
    )

    context = {
        'current_tab': 'listings',
        'all_listings': all_listings,
    }

    return render(request, 'dashboard_app/listings.html', context)


# ─────────────────────────────────────────────
# BANNED USERS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def banned_users_list(request):
    banned_list = User.objects.filter(is_active=False).order_by('-updated_at')

    context = {
        'current_tab': 'banned',
        'banned_list': banned_list,
    }

    return render(request, 'dashboard_app/banned_users.html', context)


# ─────────────────────────────────────────────
# MESSAGES PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def messages_list(request):
    all_messages = ContactMessage.objects.all().order_by('-created_at')

    context = {
        'current_tab': 'messages',
        'all_messages': all_messages,
    }

    return render(request, 'dashboard_app/messages.html', context)


# ─────────────────────────────────────────────
# APPLICATIONS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def applications_list(request):
    total_applications = Application.objects.count()

    app_stats = {
        'total': total_applications,
        'pending': Application.objects.filter(status=Application.STATUS_PENDING).count(),
        'accepted': Application.objects.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': Application.objects.filter(status=Application.STATUS_REJECTED).count(),
        'avg_compatibility': Application.objects.exclude(
            compatibility__isnull=True
        ).aggregate(avg=Avg('compatibility'))['avg'],
    }

    all_applications = (
        Application.objects.select_related('seeker', 'listing', 'listing__poster')
        .prefetch_related('listing__images')
        .order_by('-applied_at')
    )

    context = {
        'current_tab': 'applications',
        'all_applications': all_applications,
        'app_stats': app_stats,
    }

    return render(request, 'dashboard_app/applications.html', context)


# ─────────────────────────────────────────────
# VERIFICATION PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def verification_list(request):
    pending_documents = (
        VerificationDocument.objects.filter(status='pending')
        .select_related('user', 'listing')
        .order_by('created_at')
    )

    all_documents = (
        VerificationDocument.objects.select_related('user', 'listing')
        .order_by('-updated_at')
    )

    context = {
        'current_tab': 'verification',
        'pending_documents': pending_documents,
        'all_documents': all_documents,
    }

    return render(request, 'dashboard_app/verification.html', context)


# ─────────────────────────────────────────────
# REVIEWS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def reviews_list(request):
    pending_reviews = Testimonial.objects.filter(approved=False).select_related('user')
    approved_reviews = Testimonial.objects.filter(approved=True).select_related('user')

    context = {
        'current_tab': 'reviews',
        'pending_reviews': pending_reviews,
        'approved_reviews': approved_reviews,
    }

    return render(request, 'dashboard_app/reviews.html', context)


# ─────────────────────────────────────────────
# SITE CONTENT PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def site_content_page(request):
    site_content = SiteContent.load()

    context = {
        'current_tab': 'site-content',
        'site_content': site_content,
    }

    return render(request, 'dashboard_app/site_content.html', context)


# ─────────────────────────────────────────────
# SETTINGS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def settings_page(request):
    context = {
        'current_tab': 'settings',
    }

    return render(request, 'dashboard_app/settings.html', context)


# Redirect old index to overview
@user_passes_test(is_admin, login_url='/auth/login/')
def index(request):
    return redirect('dashboard_app:overview')


# ─────────────────────────────────────────────
# USER MODERATION
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def ban_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save()
    return redirect('dashboard_app:index')


@user_passes_test(is_admin, login_url='/auth/login/')
def unban_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.save()
    return redirect('dashboard_app:index')


# ─────────────────────────────────────────────
# LISTING MODERATION
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def hide_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = 'closed'
        listing.save()
    return redirect('dashboard_app:index')


@user_passes_test(is_admin, login_url='/auth/login/')
def restore_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = 'active'
        listing.save()
    return redirect('dashboard_app:index')


@user_passes_test(is_admin, login_url='/auth/login/')
def delete_listing(request, listing_id):
    if request.method == 'POST':
        get_object_or_404(Listing, id=listing_id).delete()
    return redirect('dashboard_app:index')


# ─────────────────────────────────────────────
# CONTACT MESSAGES
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def mark_message_read(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(ContactMessage, id=message_id)
        msg.is_read = True
        msg.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})

    return redirect(f"{reverse('dashboard_app:index')}#messages")


@user_passes_test(is_admin, login_url='/auth/login/')
def delete_message(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(ContactMessage, id=message_id)
        msg.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})

    return redirect(f"{reverse('dashboard_app:index')}#messages")


# ─────────────────────────────────────────────
# SITE CONTENT
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def update_site_content(request):
    if request.method == 'POST':
        content = SiteContent.load()

        editable_fields = [
            f.name for f in SiteContent._meta.get_fields()
            if f.concrete and f.name not in ('id', 'updated_at')
        ]

        for field in editable_fields:
            if field in request.POST:
                setattr(content, field, request.POST.get(field, '').strip())

        content.save()

    return redirect(f"{reverse('dashboard_app:index')}#site-content")


# ─────────────────────────────────────────────
# VERIFICATION DOCUMENTS
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def approve_document(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(VerificationDocument, id=doc_id)
        doc.status = VerificationDocument.APPROVED
        doc.rejection_reason = ''
        doc.reviewed_by = request.user
        doc.reviewed_at = timezone.now()
        doc.save()

    return redirect(f"{reverse('dashboard_app:index')}#verification")


@user_passes_test(is_admin, login_url='/auth/login/')
def reject_document(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(VerificationDocument, id=doc_id)
        doc.status = VerificationDocument.REJECTED
        doc.rejection_reason = request.POST.get('reason', '').strip()
        doc.reviewed_by = request.user
        doc.reviewed_at = timezone.now()
        doc.save()

    return redirect(f"{reverse('dashboard_app:index')}#verification")


# ─────────────────────────────────────────────
# REVIEWS MODERATION
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def approve_review(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Testimonial, id=review_id)
        review.approved = True
        review.save()

    return redirect(f"{reverse('dashboard_app:index')}#reviews")


@user_passes_test(is_admin, login_url='/auth/login/')
def reject_review(request, review_id):
    if request.method == 'POST':
        get_object_or_404(Testimonial, id=review_id).delete()
    return redirect(f"{reverse('dashboard_app:index')}#reviews")

# ── View user listings (admin only) ──────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def view_user_listings(request, user_id):
    user = get_object_or_404(User, id=user_id)
    listings = (
        Listing.objects.filter(poster=user)
        .annotate(app_count=Count('applications'))
        .order_by('-created_at')
    )

    return render(request, 'dashboard_app/view_user_listings.html', {
        'user': user,
        'listings': listings,
        'current_tab': 'users',
    })


# ── View user applications (admin only) ──────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def view_user_applications(request, user_id):
    user = get_object_or_404(User, id=user_id)
    applications = (
        Application.objects.filter(seeker=user)
        .select_related('listing', 'listing__poster')
        .order_by('-applied_at')
    )

    return render(request, 'dashboard_app/view_user_applications.html', {
        'user': user,
        'applications': applications,
        'current_tab': 'users',
    })


# ── Delete user ───────────────────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return redirect('dashboard_app:users')

    user = get_object_or_404(User, id=user_id)
    return render(request, 'dashboard_app/confirm_delete_user.html', {
        'user': user,
        'current_tab': 'users',
    })


# ── Listing detail (admin view — all applications for a room) ─────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def listing_detail(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related('poster').prefetch_related('images'),
        id=listing_id,
    )

    applications = (
        Application.objects
        .filter(listing=listing)
        .select_related('seeker')
        .order_by('-applied_at')
    )

    stats = {
        'total': applications.count(),
        'pending': applications.filter(status=Application.STATUS_PENDING).count(),
        'accepted': applications.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': applications.filter(status=Application.STATUS_REJECTED).count(),
    }

    return render(request, 'dashboard_app/listing_detail.html', {
        'listing': listing,
        'applications': applications,
        'stats': stats,
    })