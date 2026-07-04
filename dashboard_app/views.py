from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json

from accounts_app.models import User
from listings_app.models import Listing
from applications_app.models import Application
from core_app.models import SiteContent


def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin, login_url='/auth/login/')
def index(request):

    # ── Metric cards ─────────────────────────────────────────────────────────
    total_users        = User.objects.count()
    active_listings    = Listing.objects.filter(status='active').count()
    total_applications = Application.objects.count()
    banned_users       = User.objects.filter(is_active=False).count()

    # ── Activity chart — new users & listings per day (last 30 days) ─────────
    thirty_days_ago = timezone.now() - timedelta(days=30)

    users_per_day = (
        User.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    listings_per_day = (
        Listing.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    chart_users    = json.dumps([
        {'day': str(r['day']), 'count': r['count']} for r in users_per_day
    ])
    chart_listings = json.dumps([
        {'day': str(r['day']), 'count': r['count']} for r in listings_per_day
    ])

    # ── Top active cities ─────────────────────────────────────────────────────
    top_cities_qs = (
        Listing.objects
        .filter(status='active', city__isnull=False)
        .exclude(city='')
        .values('city')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    total_active = active_listings or 1          # avoid division by zero
    top_cities = [
        {
            'city':    row['city'],
            'count':   row['count'],
            'percent': round(row['count'] / total_active * 100),
        }
        for row in top_cities_qs
    ]

    # ── Most applied listings ─────────────────────────────────────────────────
    top_listings = (
        Listing.objects
        .annotate(app_count=Count('applications'))
        .order_by('-app_count')[:5]
    )

    # ── Recent users (last 10) ────────────────────────────────────────────────
    recent_users = User.objects.order_by('-created_at')[:10]

    # ── All users (for Users tab) ─────────────────────────────────────────────
    all_users = (
        User.objects
        .annotate(
            listing_count=Count('listings', distinct=True),
            application_count=Count('applications', distinct=True),
        )
        .order_by('-created_at')
    )

    # ── All listings (for Listings tab) ──────────────────────────────────────
    all_listings = (
        Listing.objects
        .select_related('poster')
        .annotate(app_count=Count('applications'))
        .order_by('-created_at')
    )

    # ── Banned users (for Banned tab) ────────────────────────────────────────
    banned_list = User.objects.filter(is_active=False).order_by('-updated_at')

    # ── Site content (for Site Content tab) ──────────────────────────────────
    site_content = SiteContent.load()

    context = {
        # cards
        'total_users':        total_users,
        'active_listings':    active_listings,
        'total_applications': total_applications,
        'banned_users':       banned_users,
        # chart
        'chart_users':        chart_users,
        'chart_listings':     chart_listings,
        # overview panels
        'top_cities':         top_cities,
        'top_listings':       top_listings,
        'recent_users':       recent_users,
        # full tabs
        'all_users':          all_users,
        'all_listings':       all_listings,
        'banned_list':        banned_list,
        'site_content':       site_content,
    }
    return render(request, 'dashboard_app/index.html', context)


# ── Ban / Unban actions ───────────────────────────────────────────────────────

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


# ── Listing moderation actions ────────────────────────────────────────────────

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
        listing = get_object_or_404(Listing, id=listing_id)
        listing.delete()
    return redirect('dashboard_app:index')


# ── Site content (landing page) ───────────────────────────────────────────────

@user_passes_test(is_admin, login_url='/auth/login/')
def update_site_content(request):
    if request.method == 'POST':
        content = SiteContent.load()

        # Every field on the model is a simple text field, so we can just
        # walk the POST data and set matching attributes — keeps this view
        # short even though SiteContent has many fields.
        editable_fields = [f.name for f in SiteContent._meta.get_fields()
                            if f.concrete and f.name not in ('id', 'updated_at')]

        for field in editable_fields:
            if field in request.POST:
                setattr(content, field, request.POST.get(field, '').strip())

        content.save()

    return redirect(f"{reverse('dashboard_app:index')}#site-content")
