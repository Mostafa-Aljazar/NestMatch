from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.html import escape
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta
import json

from accounts_app.models import User, VerificationDocument, Testimonial
from listings_app.models import Listing
from applications_app.models import Application
from core_app.models import SiteContent, ContactMessage, ContactReply


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
        Listing.objects
        .filter(created_at__gte=thirty_days_ago)
        .exclude(price__isnull=True)
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
        .exclude(price__isnull=True)
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
        Listing.objects
        .exclude(price__isnull=True)
        .annotate(app_count=Count('applications'))
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
    from django.core.paginator import Paginator

    all_listings = (
        Listing.objects.select_related('poster')
        .annotate(app_count=Count('applications'))
        .order_by('-created_at')
    )

    paginator = Paginator(all_listings, 10)  # 10 listings per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'current_tab': 'listings',
        'page_obj': page_obj,
        'all_listings': page_obj.object_list,
    }

    return render(request, 'dashboard_app/listings.html', context)


# ─────────────────────────────────────────────
# BANNED USERS PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def banned_users_list(request):
    from django.core.paginator import Paginator

    all_banned = User.objects.filter(is_active=False).order_by('-updated_at')

    paginator = Paginator(all_banned, 10)  # 10 banned users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'current_tab': 'banned',
        'page_obj': page_obj,
        'banned_list': page_obj.object_list,
    }

    return render(request, 'dashboard_app/banned_users.html', context)


# ─────────────────────────────────────────────
# MESSAGES PAGE
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
def messages_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Q

    all_messages = ContactMessage.objects.select_related('user').prefetch_related('replies__replied_by').order_by('-created_at')

    # Counts are taken before the search filter so the summary cards always
    # reflect the full inbox, not just the current search results.
    total_count = all_messages.count()
    unread_count = all_messages.filter(is_read=False).count()

    search_query = request.GET.get('q', '').strip()
    if search_query:
        all_messages = all_messages.filter(
            Q(name__icontains=search_query) | Q(email__icontains=search_query)
        )

    status_filter = request.GET.get('status', 'all')
    if status_filter == 'unread':
        all_messages = all_messages.filter(is_read=False)
    elif status_filter == 'read':
        all_messages = all_messages.filter(is_read=True)
    else:
        status_filter = 'all'

    paginator = Paginator(all_messages, 10)  # 10 messages per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'current_tab': 'messages',
        'page_obj': page_obj,
        'all_messages': page_obj.object_list,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': total_count - unread_count,
        'search_query': search_query,
        'status_filter': status_filter,
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
        user.ban_reason = request.POST.get('reason', '').strip()
        user.save()
    return redirect('dashboard_app:index')


@user_passes_test(is_admin, login_url='/auth/login/')
def unban_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.ban_reason = ''
        user.save()
    return redirect('dashboard_app:index')


# ─────────────────────────────────────────────
# LISTING MODERATION
# ─────────────────────────────────────────────
@user_passes_test(is_admin, login_url='/auth/login/')
@user_passes_test(is_admin, login_url='/auth/login/')
def hide_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = 'closed'
        listing.save()
    return redirect('dashboard_app:listings')


@user_passes_test(is_admin, login_url='/auth/login/')
def activate_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        if listing.status == 'inactive' or listing.status == 'draft':
            listing.status = 'pending'
        listing.save()
    return redirect('dashboard_app:listings')


@user_passes_test(is_admin, login_url='/auth/login/')
def approve_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        if listing.status == 'pending':
            contract_approved = listing.contract_documents.filter(
                document_type='rental_contract', status='approved'
            ).exists()
            if not contract_approved:
                messages.error(
                    request,
                    f'Cannot approve "{listing.title}" — its rental contract has not been approved yet.'
                )
            else:
                listing.status = 'active'
                listing.save()
    return redirect('dashboard_app:listings')


@user_passes_test(is_admin, login_url='/auth/login/')
def reject_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        if listing.status == 'pending':
            listing.status = 'inactive'
            listing.save()
    return redirect('dashboard_app:listings')


@user_passes_test(is_admin, login_url='/auth/login/')
def restore_listing(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        contract_approved = listing.contract_documents.filter(
            document_type='rental_contract', status='approved'
        ).exists()
        if not contract_approved:
            listing.status = 'pending'
            messages.warning(
                request,
                f'"{listing.title}" was restored to Pending — its rental contract still needs approval before it can go Active.'
            )
        else:
            listing.status = 'active'
        listing.save()
    return redirect('dashboard_app:listings')


@user_passes_test(is_admin, login_url='/auth/login/')
def delete_listing(request, listing_id):
    if request.method == 'POST':
        get_object_or_404(Listing, id=listing_id).delete()
    return redirect('dashboard_app:listings')


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


@user_passes_test(is_admin, login_url='/auth/login/')
def reply_message(request, message_id):
    """
    Sends an admin's reply as a real email to the address the visitor left
    on the Contact Us form, and marks the message read (replying to it
    implies it's been handled).
    """
    if request.method != 'POST':
        return redirect(f"{reverse('dashboard_app:index')}#messages")

    msg = get_object_or_404(ContactMessage, id=message_id)
    reply_text = request.POST.get('reply', '').strip()

    if not reply_text:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Reply message cannot be empty.'})
        return redirect(f"{reverse('dashboard_app:index')}#messages")

    subject = 'Re: Your inquiry to NestMatch Support'
    text_content = (
        f'Dear {msg.name},\n\n'
        f'Thank you for contacting NestMatch. Below is our response to your inquiry:\n\n'
        f'{reply_text}\n\n'
        f'For your reference, your original message was:\n"{msg.message}"\n\n'
        f'If you have any further questions, simply reply to this email and our team will be happy to assist.\n\n'
        f'Kind regards,\n'
        f'The NestMatch Support Team'
    )

    safe_name = escape(msg.name)
    safe_reply = escape(reply_text)
    safe_original = escape(msg.message)
    html_content = f'''
    <div style="font-family: Georgia, 'Times New Roman', serif; max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e5e9;">
      <div style="background: #A85300; padding: 28px 32px;">
        <h1 style="color: #ffffff; font-size: 19px; font-weight: 700; margin: 0; letter-spacing: .3px;">NestMatch</h1>
        <p style="color: rgba(255,255,255,0.82); font-size: 12.5px; margin: 4px 0 0; font-family: Arial, sans-serif; text-transform: uppercase; letter-spacing: .8px;">Customer Support</p>
      </div>
      <div style="padding: 36px 32px 28px; font-family: Arial, sans-serif;">
        <p style="color: #1e293b; font-size: 14.5px; line-height: 1.6; margin: 0 0 18px;">Dear {safe_name},</p>
        <p style="color: #1e293b; font-size: 14.5px; line-height: 1.6; margin: 0 0 18px;">Thank you for contacting NestMatch. Please find our response to your inquiry below.</p>

        <div style="color: #1e293b; font-size: 14.5px; line-height: 1.7; white-space: pre-wrap; margin: 0 0 26px; padding: 18px 20px; background: #FFFAF2; border-radius: 8px; border: 1px solid #FDDCC7;">{safe_reply}</div>

        <p style="color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 8px;">Your Original Message</p>
        <div style="border-left: 3px solid #D1D5DB; padding: 4px 0 4px 16px; margin: 0 0 28px;">
          <p style="color: #64748b; font-size: 13px; line-height: 1.6; margin: 0; white-space: pre-wrap; font-style: italic;">&ldquo;{safe_original}&rdquo;</p>
        </div>

        <p style="color: #1e293b; font-size: 14.5px; line-height: 1.6; margin: 0 0 4px;">Should you require further assistance, please do not hesitate to reply directly to this email.</p>
        <p style="color: #1e293b; font-size: 14.5px; line-height: 1.6; margin: 22px 0 0;">
          Kind regards,<br>
          <strong>The NestMatch Support Team</strong>
        </p>
      </div>
      <div style="background: #f8fafc; border-top: 1px solid #e5e7eb; padding: 18px 32px; text-align: center; font-family: Arial, sans-serif;">
        <p style="color: #94a3b8; font-size: 11.5px; margin: 0;">&copy; 2026 NestMatch. All rights reserved.</p>
        <p style="color: #b0b7c1; font-size: 11px; margin: 4px 0 0;">This is a reply to a message you submitted via our Contact Us form.</p>
      </div>
    </div>
    '''

    email = EmailMultiAlternatives(subject, text_content, None, [msg.email])
    email.attach_alternative(html_content, 'text/html')
    email.send()

    reply = ContactReply.objects.create(message=msg, reply_text=reply_text, replied_by=request.user)

    msg.is_read = True
    msg.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'reply': {
                'text': reply.reply_text,
                'replied_at': reply.replied_at.strftime('%b %d, %Y') + ' · ' + reply.replied_at.strftime('%H:%M'),
                'replied_by': (reply.replied_by.full_name.strip() if reply.replied_by else '') or 'Admin',
            },
        })

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
        # Rental contract approved while its listing is waiting on review — activate it.
        if doc.listing and doc.document_type == 'rental_contract' and doc.listing.status in ['pending', 'draft']:
            doc.listing.status = 'active'
            doc.listing.save()

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
        # Rental contract rejected — the listing can't stay Active without an approved contract.
        if doc.listing and doc.document_type == 'rental_contract' and doc.listing.status not in ['pending', 'closed', 'draft']:
            doc.listing.status = 'pending'
            doc.listing.save()

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


@user_passes_test(is_admin, login_url='/auth/login/')
def user_documents(request, user_id):
    user = get_object_or_404(User, id=user_id)
    documents = VerificationDocument.objects.filter(user=user).select_related('reviewed_by').order_by('-created_at')

    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')
        action = request.POST.get('action')
        doc = get_object_or_404(VerificationDocument, id=doc_id, user=user)

        if action == 'approve':
            doc.status = VerificationDocument.APPROVED
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.rejection_reason = ''
            doc.save()
        elif action == 'reject':
            doc.status = VerificationDocument.REJECTED
            doc.rejection_reason = request.POST.get('rejection_reason', '')
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save()
        elif action == 'cancel':
            doc.status = VerificationDocument.PENDING
            doc.reviewed_by = None
            doc.reviewed_at = None
            doc.rejection_reason = ''
            doc.save()

        return redirect('dashboard_app:user_documents', user_id=user_id)

    return render(request, 'dashboard_app/user_documents.html', {
        'user': user,
        'documents': documents,
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

    documents = VerificationDocument.objects.filter(
        listing=listing,
        document_type=VerificationDocument.RENTAL_CONTRACT
    ).select_related('user', 'reviewed_by')

    stats = {
        'total': applications.count(),
        'pending': applications.filter(status=Application.STATUS_PENDING).count(),
        'accepted': applications.filter(status=Application.STATUS_ACCEPTED).count(),
        'rejected': applications.filter(status=Application.STATUS_REJECTED).count(),
    }

    return render(request, 'dashboard_app/listing_detail.html', {
        'listing': listing,
        'applications': applications,
        'documents': documents,
        'stats': stats,
    })


@user_passes_test(is_admin, login_url='/auth/login/')
@user_passes_test(is_admin, login_url='/auth/login/')
def document_action(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(VerificationDocument, id=doc_id)
        action = request.POST.get('action')

        if action == 'approve':
            doc.status = VerificationDocument.APPROVED
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.rejection_reason = ''
            doc.save()
            # Set listing back to active when contract is approved (from pending status)
            if doc.listing and doc.listing.status in ['pending', 'draft']:
                doc.listing.status = 'active'
                doc.listing.save()
        elif action == 'reject':
            doc.status = VerificationDocument.REJECTED
            doc.rejection_reason = request.POST.get('rejection_reason', '')
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save()
            # Set listing to pending when contract is rejected (if not already pending/closed)
            if doc.listing and doc.listing.status not in ['pending', 'closed', 'draft']:
                doc.listing.status = 'pending'
                doc.listing.save()
        elif action == 'cancel':
            doc.status = VerificationDocument.PENDING
            cancellation_reason = request.POST.get('cancellation_reason', '')
            if cancellation_reason:
                doc.rejection_reason = f"[CANCELLED] {cancellation_reason}"
            else:
                doc.rejection_reason = ''
            doc.reviewed_by = None
            doc.reviewed_at = None
            doc.save()
            # Contract is back to pending review, so the room can't stay active.
            if doc.listing and doc.listing.status == 'active':
                doc.listing.status = 'pending'
                doc.listing.save()

        if doc.listing:
            return redirect('dashboard_app:listing_detail', listing_id=doc.listing.id)
        else:
            return redirect('dashboard_app:users')

    return redirect('dashboard_app:listings')