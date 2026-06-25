from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .models import User

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
                'form_data': request.POST # Retain input values on error
            })

        try:
            # Create the user using the structured postData method in your manager
            user = User.objects.create_user(request.POST)
            
            # Automatically establish a login session for the newly created user
            login(request, user)
            
            messages.success(request, "Registration successful! Welcome to NestMatch.")
            return redirect('core_app:index')

        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            return render(request, 'register.html', {
                'countries': User.COUNTRY_CHOICES,
                'genders': User.GENDER_CHOICES
            })

    return redirect('accounts_app:register_page_view')


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

        # Fetch the actual user instance to authenticate with Django auth core
        user_obj = User.objects.filter(email__iexact=identifier).first() or \
                   User.objects.filter(username__iexact=identifier).first()

        if user_obj:
            # Authenticate against Django backend architecture
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('core_app:index')

        messages.error(request, "Authentication failed. Invalid credentials.")
        return render(request, 'login.html')

    return render(request, 'login.html')

def profile_view(request):
    return render(request, 'profile.html')


# def password_reset_view(request):
#     return render(request, 'register.html')


# def logout_view(request):
#     return HttpResponse("<h1>Logout</h1>")
