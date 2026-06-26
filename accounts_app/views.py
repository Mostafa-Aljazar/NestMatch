from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import User, LifestyleProfile


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
            # Loop through all found errors and pass them to Django messages framework
            for key, val in errors.items():
                messages.error(request, val)
            return render(request, 'register.html', {
                'countries': User.COUNTRY_CHOICES,
                'genders': User.GENDER_CHOICES,
                'form_data': request.POST  # Retain input values on error
            })

        try:
            # Create the user using the structured postData method in your manager
            user = User.objects.create_user(request.POST)

            # Automatically establish a login session for the newly created user
            login(request, user)

            messages.success(request, "Registration successful! Welcome to NestMatch.")
            return redirect('accounts_app:profile')

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
            for key, val in errors.items():
                messages.error(request, val)
            return render(request, 'login.html')

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
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('accounts_app:profile')

        messages.error(request, "Authentication failed. Invalid credentials.")
        return render(request, 'login.html')

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
        for key, val in errors.items():
            messages.error(request, val)
        return redirect('accounts_app:profile')

    User.objects.update_profile(user, request.POST, request.FILES)
    messages.success(request, "Your personal information has been updated.")
    return redirect('accounts_app:profile')


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
        for key, val in errors.items():
            messages.error(request, val)
        return redirect('accounts_app:profile')

    LifestyleProfile.objects.save_for_user(request.user, request.POST)
    messages.success(request, "Your lifestyle profile has been updated.")
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
        messages.error(request, "Current password is incorrect.")
        return redirect('accounts_app:profile')

    if len(new_password) < 8:
        messages.error(request, "New password must be at least 8 characters!")
        return redirect('accounts_app:profile')

    if new_password != confirm_password:
        messages.error(request, "New passwords do not match!")
        return redirect('accounts_app:profile')

    user.set_password(new_password)
    user.save()
    # Keeps the current session valid after the password hash changes
    update_session_auth_hash(request, user)

    messages.success(request, "Your password has been updated.")
    return redirect('accounts_app:profile')