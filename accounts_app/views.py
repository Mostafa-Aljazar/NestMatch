from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse,FileResponse, Http404
from .models import User, LifestyleProfile, Testimonial ,OTPCode ,VerificationDocument
from django.core.mail import EmailMultiAlternatives
from listings_app.models import Listing
import mimetypes , os


def index(request):
    """
    Renders the main home page or landing view.
    """
    return render(request, 'register.html')


def register_page_view(request):
    """
    Displays the registration page to the user.
    """
    # Context dictionary sending choices to populate dropdown fields dynamically
    context = {
        'countries': User.COUNTRY_CHOICES,
        'genders': User.GENDER_CHOICES,
    }
    return render(request, 'register.html', context)


def register_create_view(request):
    """
    Processes the custom registration logic using UserManager validators.
    NOTE: Django's CsrfViewMiddleware automatically protects this POST view
    as long as the register.html form includes {% csrf_token %}.
    """
    if request.method == 'POST':
        # Validate the form input fields using the custom manager method
        errors = User.objects.register_validator(request.POST)

        if errors:
            return render(request, 'register.html', {
                'countries': User.COUNTRY_CHOICES,
                'genders': User.GENDER_CHOICES,
                'form_data': request.POST,
                'errors': errors,          
            })

        try:
            # Create the user using the structured postData method in your manager
            user = User.objects.create_user(request.POST)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            # Automatically establish a login session for the newly created user
            login(request, user)
            #messages.success(request, "Registration successful! Welcome to NestMatch.")
            return redirect('listings_app:listings')

        except Exception:
            messages.error(request, "An unexpected error occurred. Please try again.")
            return render(request, 'register.html', {
                'countries': User.COUNTRY_CHOICES,
                'genders': User.GENDER_CHOICES
            })
        
    return redirect('accounts_app:register_page')


def login_view(request):
    """
    Authenticates user credentials using custom login validator logic.
    """
    if request.method == 'POST':
        # Pass the POST data directly to the login custom validation rules
        errors = User.objects.login_validator(request.POST)

        if errors:
            error_msg = list(errors.values())[0]
            return render(request, 'login.html', {'error': error_msg})

        # Extract identifier (which checks both email/username inside the manager)
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Fetch the actual user instance to authenticate with Django auth core.
        # (login_validator already looked this user up internally to check the
        # password; we re-fetch here by identifier since the validator doesn't
        # return the instance itself — this keeps the two functions independent.)
        user_obj = User.objects.filter(email__iexact=identifier).first() or \
                   User.objects.filter(username__iexact=identifier).first()

        if user_obj:
            # A banned account (is_active=False) makes Django's authenticate()
            # return None even with the correct password, same as a wrong
            # password would -- so check the password against it directly
            # first to tell the two cases apart and redirect banned users to
            # a clear notice instead of a generic "invalid credentials" error.
            if not user_obj.is_active and user_obj.check_password(password):
                return redirect(f"{reverse('accounts_app:login')}?banned=1")

            # Authenticate against Django backend architecture
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                #messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('listings_app:listings')

        return render(request, 'login.html', {'errors': {'email': 'Invalid email/username or password.'}})

    return render(request, 'login.html')


@login_required
def profile_view(request):
    """
    Renders the account settings / profile page with REAL data:
    - the logged-in user's personal info (for the "Personal info" tab)
    - their lifestyle profile, if one exists (for the "Lifestyle profile" tab)
    - the full choice lists, so dropdowns/option-cards can mark the
      user's current selection as selected/active instead of showing
      hardcoded placeholder values.

    @login_required redirects anonymous visitors to the login page
    instead of leaking another user's settings page.
    """
    user = request.user

    # Read ?tab= from URL so the template can set initial active state
    # even before JS runs (progressive enhancement)
    active_tab = request.GET.get('tab', 'info')
    valid_tabs = {'info', 'lifestyle', 'security', 'reviews'}
    if active_tab not in valid_tabs:
        active_tab = 'info'

    # A user might not have filled out their lifestyle profile yet,
    # so this can legitimately be None — the template handles that case.
    lifestyle_profile = LifestyleProfile.objects.filter(user=user).first()

    # Completeness score: photo/bio/phone are each worth 25% (all-or-nothing),
    # and the last 25% scales with how much of the lifestyle questionnaire is
    # filled in (LifestyleProfile.completeness_fraction) rather than a flat
    # "profile exists or not" checkbox — so filling in more of the extended
    # preference fields visibly moves the needle.
    lifestyle_completeness = lifestyle_profile.completeness_fraction if lifestyle_profile else 0.0
    lifestyle_fields_filled = lifestyle_profile.fields_filled_count if lifestyle_profile else 0
    lifestyle_fields_total = len(LifestyleProfile.ALL_PREFERENCE_FIELDS)
    profile_strength = round(100 * (
      (bool(user.profile_pic) + bool(user.is_id_verified) + bool(user.phone_number) + lifestyle_completeness) / 4
    ))

    documents = {d.document_type: d for d in user.verification_documents.all()}
    verification_cards = [
        ('id_document', 'ID Document', documents.get('id_document')),
    ]
    # جيبي الغرف المنشورة للمستخدم
    user_listings = Listing.objects.filter(poster=user, status='active')

    rental_contract_doc = documents.get('rental_contract')
    contract_docs = {
        d.listing_id: d
        for d in user.verification_documents.filter(document_type='rental_contract')
    }
    context = {
        'user_obj': user,  # named user_obj to avoid clashing with request.user in template logic
        'genders': User.GENDER_CHOICES,
        'countries': User.COUNTRY_CHOICES,
        'lifestyle_profile': lifestyle_profile,
        'profile_strength': profile_strength,
        'lifestyle_completeness_pct': round(lifestyle_completeness * 100),
        'lifestyle_fields_filled': lifestyle_fields_filled,
        'lifestyle_fields_total': lifestyle_fields_total,
        'sleep_time_choices': LifestyleProfile.SLEEP_TIME_CHOICES,
        'wake_time_choices': LifestyleProfile.WAKE_TIME_CHOICES,
        'noise_level_choices': LifestyleProfile.NOISE_LEVEL_CHOICES,
        'cleanliness_choices': LifestyleProfile.CLEANLINESS_CHOICES,
        'social_type_choices': LifestyleProfile.SOCIAL_TYPE_CHOICES,
        'preferred_roommates_choices': LifestyleProfile.PREFERRED_ROOMMATES_CHOICES,
        'religion_choices': LifestyleProfile.RELIGION_CHOICES,
        'field_choices': LifestyleProfile.FIELD_CHOICES,
        'smoking_choices': LifestyleProfile.SMOKING_CHOICES,
        'roommate_gender_pref_choices': LifestyleProfile.ROOMMATE_GENDER_PREF_CHOICES,
        'dietary_choices': LifestyleProfile.DIETARY_CHOICES,
        'guest_tolerance_choices': LifestyleProfile.GUEST_TOLERANCE_CHOICES,
        'tenant_type_choices': LifestyleProfile.TENANT_TYPE_CHOICES,
        'household_lang_pref_choices': LifestyleProfile.HOUSEHOLD_LANG_PREF_CHOICES,
        'min_stay_pref_choices': LifestyleProfile.MIN_STAY_PREF_CHOICES,
        'listing_type_pref_choices': LifestyleProfile.LISTING_TYPE_PREF_CHOICES,
        'user_reviews': Testimonial.objects.filter(user=user).order_by('-created_at'),
        'review_section_heading': 'Write a review',
        'rental_contract_doc': rental_contract_doc,
        'verification_cards': verification_cards,
        'active_tab': active_tab,
        'user_listings': user_listings,
        'contract_docs': contract_docs,
    }
    return render(request, 'profile.html', context)


@login_required
def public_profile_view(request, user_id):
    """
    Read-only profile page for viewing ANOTHER user — a poster checking
    out a seeker who applied to their room, or a seeker checking out the
    poster before applying. No edit forms, no security tab, no email/phone
    (those stay private to the profile owner).
    """
    profile_user = get_object_or_404(User, pk=user_id)

    # Viewing your own public profile link just sends you to the real
    # (editable) profile page instead of a read-only mirror of it.
    if profile_user.pk == request.user.pk:
        return redirect('accounts_app:profile')

    lifestyle_profile = LifestyleProfile.objects.filter(user=profile_user).first()
    active_listings = profile_user.listings.filter(status='active').prefetch_related('images').order_by('-created_at')
    listing_count = active_listings.count()
    shown_listings = active_listings[:4]

    # Contact Us submissions are private support inquiries -- only staff
    # reviewing a user's profile from the admin dashboard should see them,
    # never a regular seeker/poster looking at someone else's profile.
    contact_messages = None
    submitted_reviews = None
    if request.user.is_staff:
        contact_messages = profile_user.contact_messages.order_by('-created_at')
        submitted_reviews = profile_user.testimonials.order_by('-created_at')

    context = {
        'profile_user': profile_user,
        'lifestyle_profile': lifestyle_profile,
        'listing_count': listing_count,
        'active_listings': shown_listings,
        'more_listings_count': max(0, listing_count - len(shown_listings)),
        'contact_messages': contact_messages,
        'submitted_reviews': submitted_reviews,
    }
    return render(request, 'public_profile.html', context)


@login_required
@require_POST  # this view only ever makes sense as a POST; GET here is a 405, not a silent no-op
def profile_update_personal_info(request):
    """
    Handles the "Personal info" form submission on the profile page.
    Separate endpoint from the lifestyle form, per the two-forms design:
    each tab/form posts independently, so an error in one never wipes
    out unsaved or already-saved data in the other.

    CSRF: protected automatically by Django's CsrfViewMiddleware, as
    long as the form in profile.html includes {% csrf_token %}.
    """
    user = request.user
    errors = User.objects.update_profile_validator(user, request.POST, request.FILES)

    if errors:
        return JsonResponse({'success': False, 'errors': errors})

    User.objects.update_profile(user, request.POST, request.FILES)
    user.refresh_from_db()
    pic_url = user.profile_pic.url if user.profile_pic else None
    return JsonResponse({'success': True, 'message': 'Your personal information has been updated.','profile_pic_url': pic_url, })



@login_required
@require_POST
def profile_update_lifestyle(request):
    """
    Handles the "Lifestyle profile" form submission on the profile page.
    Validates and then creates/updates the user's single LifestyleProfile
    row (one-to-one, matching the UNIQUE user_id constraint in the schema).
    """
    errors = LifestyleProfile.objects.lifestyle_validator(request.POST)

    if errors:
        return JsonResponse({'success': False, 'errors': errors})

    LifestyleProfile.objects.save_for_user(request.user, request.POST)
    return JsonResponse({'success': True, 'message': 'Your lifestyle profile has been updated.'})


@login_required
@require_POST
def submit_review(request):
    """Handle new testimonial submission — returns JSON for AJAX calls."""
    review_text   = request.POST.get('review_text', '').strip()
    reviewer_name = request.POST.get('reviewer_name', '').strip()
    role          = request.POST.get('role', '').strip()
    rating_raw    = request.POST.get('rating', '').strip()

    errors = {}
    if not reviewer_name:
        errors['reviewer_name'] = 'Your name is required.'
    if not review_text or len(review_text) < 20:
        errors['review_text'] = 'Please write a review with at least 20 characters.'
    if role not in dict(Testimonial.ROLE_CHOICES):
        errors['role'] = 'Please select your role.'

    rating = 5
    if rating_raw:
        if rating_raw.isdigit() and 1 <= int(rating_raw) <= 5:
            rating = int(rating_raw)
        else:
            errors['rating'] = 'Please select a rating between 1 and 5 stars.'
    else:
        errors['rating'] = 'Please select a star rating.'

    if errors:
        return JsonResponse({'success': False, 'errors': errors})

    Testimonial.objects.create(
        user=request.user,
        reviewer_name=reviewer_name,
        role=role,
        quote=review_text,
        rating=rating,
        approved=False,
    )

    return JsonResponse({'success': True, 'message': 'Your review has been submitted for approval.'})


@login_required
@require_POST
def delete_review(request, review_id):
    """Allow the logged-in user to delete one of their submitted reviews — returns JSON."""
    review = get_object_or_404(Testimonial, pk=review_id, user=request.user)
    review.delete()
    return JsonResponse({'success': True, 'message': 'Review removed.'})


@login_required
@require_POST
def change_password_view(request):
    """
    Handles the "Change password" form on the Security tab.
    Verifies the current password before allowing a change, and keeps
    the user logged in afterwards (Django logs a user out of their
    session if their password hash changes mid-session unless we
    explicitly update the session auth hash).
    """
    from django.contrib.auth import update_session_auth_hash

    user = request.user
    new_password     = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    # Google users have no current password — skip the check
    if user.auth_provider != 'google':
        current_password = request.POST.get('current_password', '')
        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'errors': {'current_password': 'Current password is incorrect.'}})

    if len(new_password) < 8:
        return JsonResponse({'success': False, 'errors': {'new_password': 'Password must be at least 8 characters!'}})

    if new_password != confirm_password:
        return JsonResponse({'success': False, 'errors': {'confirm_password': 'Passwords do not match!'}})

    user.set_password(new_password)
    if user.auth_provider == 'google':
        user.auth_provider = 'email'  # يصير يقدر يدخل بالطريقتين
    user.save()
    update_session_auth_hash(request, user)

    msg = 'Password set successfully. You can now log in with email & password.' if user.auth_provider == 'google' else 'Your password has been updated.'
    return JsonResponse({'success': True, 'message': msg})

@login_required
@require_POST
def delete_account_view(request):
    """
    Permanently deletes the logged-in user's account.
    Triggered by the "Confirm" button in the delete-account popup/modal
    (no password re-entry — confirmation is just the Confirm click itself).

    request.user.delete() cascades to LifestyleProfile via on_delete=CASCADE,
    so the lifestyle row is removed automatically — no orphaned data.
    """
    user = request.user
    user.delete()

    # The DB row is gone, but the session still thinks it's logged in
    # until we clear it explicitly.
    logout(request)

    return JsonResponse({'success': True, 'redirect_url': '/auth/register/'})

def logout_view(request):
    logout(request)
    return redirect('core_app:index')


def _send_otp_email(user, otp):
    """
    Sends a styled HTML email containing the OTP code to the user.
    Falls back to plain text for email clients that don't support HTML.
    """
    subject      = 'Your NestMatch Password Reset Code'
    text_content = f'Your verification code is: {otp.code}\n\nThis code expires in 2 minutes.'
    html_content = f'''
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e5e7eb;">

      <!-- Header -->
      <div style="background: linear-gradient(135deg, #A85300, #A85300, #CC6600); padding: 32px 24px; text-align: center;">
        <h1 style="color: #ffffff; font-size: 22px; font-weight: 800; margin: 0;"> NestMatch</h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 14px; margin: 8px 0 0;">Password Reset Code</p>
      </div>

      <!-- Body -->
      <div style="padding: 32px 24px;">
        <p style="color: #1e293b; font-size: 15px; margin: 0 0 24px;">Hi there! Here's your verification code:</p>

        <!-- OTP Code -->
        <div style="background: #FFFAF2; border: 2px solid #CC6600; border-radius: 12px; padding: 24px; text-align: center; margin: 0 0 24px;">
          <p style="color: #A85300; font-size: 42px; font-weight: 800; letter-spacing: 12px; margin: 0;">{otp.code}</p>
        </div>

        <p style="color: #64748b; font-size: 13px; margin: 0 0 8px;"> This code expires in <strong>2 minutes</strong>.</p>
        <p style="color: #64748b; font-size: 13px; margin: 0;">If you didn't request this, you can safely ignore this email.</p>
      </div>

      <!-- Footer -->
      <div style="background: #f8fafc; border-top: 1px solid #e5e7eb; padding: 16px 24px; text-align: center;">
        <p style="color: #94a3b8; font-size: 12px; margin: 0;">© 2026 NestMatch. All rights reserved.</p>
      </div>

    </div>
    '''

    msg = EmailMultiAlternatives(subject, text_content, None, [user.email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()

def forgot_password_view(request):
    """
    Displays the forgot password form.
    On POST: looks up the user by email, generates an OTP,
    sends it via email, and redirects to the verify page.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        # Check if a user with this email exists
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return render(request, 'forgot_password.html', {
                'error': 'No account found with this email address.'
            })

        # Generate a fresh 4-digit OTP and save it to the DB
        otp = OTPCode.generate_for_user(user)

        # Send the styled OTP email
        _send_otp_email(user, otp)

        # Store the user's email in session so verify/reset views know who we're resetting for
        request.session['reset_email'] = user.email

        return redirect('accounts_app:verify_otp')

    return render(request, 'forgot_password.html')


def verify_otp_view(request):
    """
    Displays the OTP verification form with a 2-minute countdown.
    On POST: checks the code against the DB — must be unused and not expired.
    On success: sets a session flag and redirects to reset password page.
    """
    # If no email in session, the user didn't go through forgot_password first
    if not request.session.get('reset_email'):
        return redirect('accounts_app:forgot_password')

    if request.method == 'POST':
        code  = request.POST.get('code', '').strip()
        email = request.session.get('reset_email')

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return redirect('accounts_app:forgot_password')

        # Find the latest unused OTP for this user
        otp = OTPCode.objects.filter(user=user, is_used=False).first()

        if not otp:
            return render(request, 'verify_otp.html', {
                'error': 'No active code found. Please request a new one.'
            })

        if otp.is_expired:
            return render(request, 'verify_otp.html', {
                'error': 'Your code has expired. Please request a new one.'
            })

        if otp.code != code:
            return render(request, 'verify_otp.html', {
                'error': 'Incorrect code. Please try again.'
            })

        # Mark the OTP as used so it can't be reused
        otp.is_used = True
        otp.save()

        # Set a session flag allowing access to the reset password page
        request.session['otp_verified'] = True

        return redirect('accounts_app:reset_password')

    return render(request, 'verify_otp.html')


def resend_otp_view(request):
    """
    Generates a new OTP and resends it to the user's email.
    Only accessible via POST to prevent accidental resends.
    Redirects back to the verify page after sending.
    """
    email = request.session.get('reset_email')

    if not email:
        return redirect('accounts_app:forgot_password')

    user = User.objects.filter(email__iexact=email).first()

    if not user:
        return redirect('accounts_app:forgot_password')

    # Generate a new OTP (this also invalidates the previous one)
    otp = OTPCode.generate_for_user(user)

    # Send the styled OTP email
    _send_otp_email(user, otp)

    return redirect('accounts_app:verify_otp')


def reset_password_view(request):
    """
    Displays the new password form.
    Only accessible if the user has verified their OTP (session flag).
    On POST: validates and saves the new password, clears session flags.
    """
    # Block direct access without OTP verification
    if not request.session.get('otp_verified'):
        return redirect('accounts_app:forgot_password')

    if request.method == 'POST':
        new_password     = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if len(new_password) < 8:
            return render(request, 'reset_password.html', {
                'error': 'Password must be at least 8 characters.'
            })

        if new_password != confirm_password:
            return render(request, 'reset_password.html', {
                'error': 'Passwords do not match.'
            })

        email = request.session.get('reset_email')
        user  = User.objects.filter(email__iexact=email).first()

        if not user:
            return redirect('accounts_app:forgot_password')

        # Save the new password
        user.set_password(new_password)
        user.save()

        # Clear all reset-related session data
        del request.session['reset_email']
        del request.session['otp_verified']

        return redirect('accounts_app:login')

    return render(request, 'reset_password.html')

@login_required
@require_POST
def verification_view(request):
    document_type = request.POST.get('document_type')
    file = request.FILES.get('file')

    if document_type not in dict(VerificationDocument.DOCUMENT_TYPE_CHOICES):
        return JsonResponse({'success': False, 'errors': {'document_type': 'Invalid document type.'}})

    if not file:
        return JsonResponse({'success': False, 'errors': {'file': 'Please choose a file to upload.'}})

    listing = None
    if document_type == VerificationDocument.RENTAL_CONTRACT:
        listing_id = request.POST.get('listing_id')
        listing = get_object_or_404(Listing, id=listing_id, poster=request.user)

    # Block re-upload once a document has already been approved — an
    # approved ID/contract shouldn't be silently swapped for a different
    # file after the fact. Resubmission is only allowed while pending or
    # after a rejection.
    existing_lookup = {'user': request.user, 'document_type': document_type}
    if listing is not None:
        existing_lookup['listing'] = listing
    existing_doc = VerificationDocument.objects.filter(**existing_lookup).first()
    if existing_doc and existing_doc.status == VerificationDocument.APPROVED:
        return JsonResponse({
            'success': False,
            'errors': {'file': 'This document has already been approved and cannot be replaced.'},
        })
    
    error = VerificationDocument.objects.validate_upload(file)
    if error:
        return JsonResponse({'success': False, 'errors': {'file': error}})

    document = VerificationDocument.objects.submit_document(
        request.user, document_type, file, listing=listing
    )

    return JsonResponse({
        'success': True,
        'message': 'Document submitted for review.',
        'document_type': document.document_type,
        'listing_id': listing.id if listing else None,
        'status': document.status,
        'status_display': document.get_status_display(),
        'updated_at': document.updated_at.strftime('%b %d, %Y').replace(' 0', ' '),
    })


@login_required
def serve_verification_document(request, doc_id):
    """
    Protected file access — serves the actual ID/contract file ONLY to its
    owner or to staff. This is why we don't link directly to document.file.url
    in templates; always link to this view instead (see urls.py note).
    """
    document = get_object_or_404(VerificationDocument, id=doc_id)
    if document.user_id != request.user.id and not request.user.is_staff:
        raise Http404

    filename = os.path.basename(document.file.name)
    content_type, _ = mimetypes.guess_type(filename)

    return FileResponse(
        document.file.open('rb'),
        filename=filename,
        content_type=content_type or 'application/octet-stream',
        as_attachment=False,  # خليها False حتى تنفتح بالمتصفح (PDF/صورة) بدل ما تتحمل
    )