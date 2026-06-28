from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import User, LifestyleProfile, Testimonial


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

    # A user might not have filled out their lifestyle profile yet,
    # so this can legitimately be None — the template handles that case.
    lifestyle_profile = LifestyleProfile.objects.filter(user=user).first()

    # Simple completeness score: personal info fields (out of 4 "nice to have"
    # fields beyond the required ones) + whether a lifestyle profile exists at all.
    # This replaces the previously hardcoded "72%" in the template.
    optional_fields_filled = sum([
        bool(user.phone_number),
        bool(user.bio),
        bool(user.profile_pic),
        lifestyle_profile is not None,
    ])
    profile_strength = int((optional_fields_filled / 4) * 100)

    context = {
        'user_obj': user,  # named user_obj to avoid clashing with request.user in template logic
        'genders': User.GENDER_CHOICES,
        'countries': User.COUNTRY_CHOICES,
        'lifestyle_profile': lifestyle_profile,
        'profile_strength': profile_strength,
        'sleep_time_choices': LifestyleProfile.SLEEP_TIME_CHOICES,
        'wake_time_choices': LifestyleProfile.WAKE_TIME_CHOICES,
        'noise_level_choices': LifestyleProfile.NOISE_LEVEL_CHOICES,
        'cleanliness_choices': LifestyleProfile.CLEANLINESS_CHOICES,
        'social_type_choices': LifestyleProfile.SOCIAL_TYPE_CHOICES,
        'preferred_roommates_choices': LifestyleProfile.PREFERRED_ROOMMATES_CHOICES,
        'religion_choices': LifestyleProfile.RELIGION_CHOICES,
        'field_choices': LifestyleProfile.FIELD_CHOICES,
        'smoking_choices': LifestyleProfile.SMOKING_CHOICES,
        'user_reviews': Testimonial.objects.filter(user=user).order_by('-created_at'),
        'review_section_heading': 'Write a review',
    }
    return render(request, 'profile.html', context)


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
    return JsonResponse({'success': True, 'message': 'Your personal information has been updated.'})


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
    """Handle new testimonial submission from the profile page."""
    review_text = request.POST.get('review_text', '').strip()
    reviewer_name = request.POST.get('reviewer_name', '').strip()
    role = request.POST.get('role')
    location = request.POST.get('location', '').strip()

    errors = {}
    if not reviewer_name:
        errors['reviewer_name'] = 'Your name is required.'

    if not review_text or len(review_text) < 20:
        errors['review_text'] = 'Please write a review with at least 20 characters.'

    if role not in dict(Testimonial.ROLE_CHOICES):
        errors['role'] = 'Please select your role.'

    if errors:
        for error_message in errors.values():
            messages.error(request, error_message)
        return redirect('accounts_app:profile')

    testimonial = Testimonial.objects.create(
        user=request.user,
        reviewer_name=reviewer_name,
        role=role,
        location=location,
        quote=review_text,
        approved=False,
    )

    messages.success(request, 'Your review has been submitted for approval.')
    return redirect('accounts_app:profile')


@login_required
@require_POST
def delete_review(request, review_id):
    """Allow the logged-in user to delete one of their submitted reviews."""
    review = get_object_or_404(Testimonial, pk=review_id, user=request.user)
    review.delete()
    messages.success(request, 'Your review has been removed.')
    return redirect('accounts_app:profile')


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
    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if not user.check_password(current_password):
        return JsonResponse({'success': False, 'errors': {'current_password': 'Current password is incorrect.'}})

    if len(new_password) < 8:
        return JsonResponse({'success': False, 'errors': {'new_password': 'New password must be at least 8 characters!'}})

    if new_password != confirm_password:
        return JsonResponse({'success': False, 'errors': {'confirm_password': 'New passwords do not match!'}})

    user.set_password(new_password)
    user.save()
    # Keeps the current session valid after the password hash changes
    update_session_auth_hash(request, user)

    return JsonResponse({'success': True, 'message': 'Your password has been updated.'})


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
    return redirect('accounts_app:login')