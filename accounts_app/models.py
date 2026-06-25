from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import date
import re
from PIL import Image, UnidentifiedImageError

class UserManager(BaseUserManager):
    # Regex patterns for validating username and email formats
    USERNAME_REGEX = r'^[a-zA-Z0-9_.]{3,30}$'
    EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'
    MIN_AGE = 18  

    # Helper method to calculate age based on date of birth
    def _calculate_age(self, dob):
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # Validator for the user registration form fields
    def register_validator(self, postData):
        errors = {}

        if len(postData.get('first_name', '').strip()) < 2:
            errors['first_name'] = 'First name must be at least 2 characters!'

        if len(postData.get('last_name', '').strip()) < 2:
            errors['last_name'] = 'Last name must be at least 2 characters!'

        username = postData.get('username', '').strip()
        if not re.match(self.USERNAME_REGEX, username):
            errors['username'] = 'Username must be 3-30 characters (letters, numbers, _ or . only)!'
        elif self.filter(username__iexact=username).exists():
            errors['username'] = 'Username already taken!'

        email = postData.get('email', '').strip()
        if not re.match(self.EMAIL_REGEX, email):
            errors['email'] = 'Invalid email format!'
        elif self.filter(email__iexact=email).exists():
            errors['email'] = 'Email already exists!'

        if len(postData.get('password', '')) < 8:
            errors['password'] = 'Password must be at least 8 characters!'
        elif postData.get('password') != postData.get('confirm_pw'):
            errors['password'] = 'Passwords do not match!'

        dob_str = postData.get('date_of_birth', '')
        if not dob_str:
            errors['date_of_birth'] = 'Date of birth is required!'
        else:
            try:
                dob = date.fromisoformat(dob_str)
                if dob > date.today():
                    errors['date_of_birth'] = 'Date of birth cannot be in the future!'
                elif self._calculate_age(dob) < self.MIN_AGE:
                    errors['date_of_birth'] = f'You must be at least {self.MIN_AGE} years old to register!'
            except ValueError:
                errors['date_of_birth'] = 'Invalid date format!'

        if postData.get('gender') not in dict(User.GENDER_CHOICES):
            errors['gender'] = 'Please select a gender!'

        if postData.get('country') not in dict(User.COUNTRY_CHOICES):
            errors['country'] = 'Please select your country!'

        return errors

    # Creates and saves a regular user with Django's built-in password hashing
    def create_user(self, postData):
        user = self.model(
            first_name=postData.get('first_name', '').strip(),
            last_name=postData.get('last_name', '').strip(),
            username=postData.get('username', '').strip(),
            email=self.normalize_email(postData.get('email', '').strip().lower()),
            date_of_birth=postData.get('date_of_birth'),
            gender=postData.get('gender', ''),
            country=postData.get('country', ''),
        )
        # Hashes and sets the password securely using Django's auth system
        user.set_password(postData.get('password')) 
        user.save(using=self._db)
        return user

    # Creates and saves a superuser (admin) via the terminal command line
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Default fallback values to prevent admin creation from breaking on model requirements
        extra_fields.setdefault('date_of_birth', '2000-01-01') 
        extra_fields.setdefault('gender', 'M')
        extra_fields.setdefault('country', 'other')

        user = self.model(username=username, email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Validator for the user login credentials (checks both username and email)
    def login_validator(self, postData):
        errors = {}
        identifier = postData.get('email', '').strip()  
        if not identifier:
            errors['email'] = 'Email or username is required!'
        else:
            user = self.filter(
                models.Q(email__iexact=identifier) | models.Q(username__iexact=identifier)
            ).first()
            if not user:
                errors['email'] = 'Invalid email/username or password!'
            # Checks the raw password against the hashed password stored in the database
            elif not user.check_password(postData.get('password', '')):
                errors['password'] = 'Invalid email/username or password!'
        return errors

    # Validator for updating user profile settings and checking image files
    def update_profile_validator(self, user, postData, files):
        errors = {}
        email = postData.get('email', '').strip()
        if not re.match(self.EMAIL_REGEX, email):
            errors['email'] = 'Invalid email format!'
        elif self.filter(email__iexact=email).exclude(id=user.id).exists():
            errors['email'] = 'This email is already in use by another account!'

        username = postData.get('username', '').strip()
        if not re.match(self.USERNAME_REGEX, username):
            errors['username'] = 'Username must be 3-30 characters (letters, numbers, _ or . only)!'
        elif self.filter(username__iexact=username).exclude(id=user.id).exists():
            errors['username'] = 'Username already taken!'

        profile_pic = files.get('profile_pic')
        if profile_pic:
            max_size = 5 * 1024 * 1024
            if profile_pic.size > max_size:
                errors['profile_pic'] = 'Profile picture must be smaller than 5MB!'
            else:
                try:
                    img = Image.open(profile_pic)
                    img.verify()
                    if img.format not in ['JPEG', 'PNG', 'WEBP', 'GIF']:
                        errors['profile_pic'] = 'Profile picture must be a JPEG, PNG, WEBP, or GIF image!'
                except Exception:
                    errors['profile_pic'] = 'Uploaded file is not a valid image!'
                finally:
                    profile_pic.seek(0)
        return errors

    # Updates and saves user profile text fields and uploaded profile picture
    def update_profile(self, user, postData, files):
        user.email = postData.get('email', user.email).strip()
        user.username = postData.get('username', user.username).strip()
        user.bio = postData.get('bio', user.bio)
        if files.get('profile_pic'):
            user.profile_pic = files['profile_pic']
        user.save()
        return user


# Custom User Model inheriting Django's built-in auth capabilities and permissions
class User(AbstractBaseUser, PermissionsMixin):
    # Choices for gender and country fields dropdowns
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    COUNTRY_CHOICES = [
        ('egyptian', 'Egyptian'), ('palestinian', 'Palestinian'),
        ('saudi', 'Saudi Arabian'), ('jordanian', 'Jordanian'),
        ('syrian', 'Syrian'), ('emirati', 'Emirati'),
        ('moroccan', 'Moroccan'), ('other', 'Other'),
    ]

    # Core user fields
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=30, unique=True)       
    email = models.EmailField(max_length=255, unique=True)
    
    # Note: 'password' field is automatically provided by AbstractBaseUser, no manual field needed
    
    # Custom profile and demographic fields
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Mandatory operational flags required for Django's admin panel access
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Links the custom manager to handle user queries and operations
    objects = UserManager()

    # Django specific settings to identify the main login field and superuser creation prompts
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email'] 

    class Meta:
        ordering = ['-created_at']

    # Returns string representation of the object (shows in Admin dashboard)
    def __str__(self):
        return f'{self.username} ({self.email})'

    # Property method to return user's full name dynamically
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    # Property method to calculate the current age dynamically
    @property
    def age(self):
        return User.objects._calculate_age(self.date_of_birth)