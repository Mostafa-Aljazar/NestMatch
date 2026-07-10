from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import date
from PIL import Image, UnidentifiedImageError
from django.utils import timezone
import uuid ,random , re
from pathlib import Path

class UserManager(BaseUserManager):
    # Regex patterns for validating username and email formats
    USERNAME_REGEX = r'^[a-zA-Z0-9_.]{3,30}$'
    EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'
    # Basic international phone format: optional leading +, 7-15 digits/spaces/dashes
    PHONE_REGEX = r'^\+?[0-9\s\-]{7,20}$'
    MIN_AGE = 18

    # Helper method to calculate age based on date of birth
    def _calculate_age(self, dob):
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # Shared helper so register/update don't duplicate date-of-birth logic
    def _validate_dob(self, dob_str):
        """Returns an error string, or None if the date of birth is valid."""
        if not dob_str:
            return 'Date of birth is required!'
        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            return 'Invalid date format!'
        if dob > date.today():
            return 'Date of birth cannot be in the future!'
        if self._calculate_age(dob) < self.MIN_AGE:
            return f'You must be at least {self.MIN_AGE} years old to register!'
        return None

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

        dob_error = self._validate_dob(postData.get('date_of_birth', ''))
        if dob_error:
            errors['date_of_birth'] = dob_error

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
            # Parse to a real date object here (not just a string) so that
            # in-memory use right after creation (e.g. user.age) works
            # correctly even before the object is reloaded from the DB.
            date_of_birth=date.fromisoformat(postData.get('date_of_birth')),
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

    # Validator for updating user profile settings and checking image files.
    # Hardened to match register_validator: now also checks phone, gender,
    # and date_of_birth (previously only email/username/picture were checked,
    # which meant a bad phone number, gender, or DOB would silently fail to save).
    def update_profile_validator(self, user, postData, files):
        errors = {}

        if len(postData.get('first_name', '').strip()) < 2:
            errors['first_name'] = 'First name must be at least 2 characters!'

        if len(postData.get('last_name', '').strip()) < 2:
            errors['last_name'] = 'Last name must be at least 2 characters!'

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

        # Phone is optional, but if provided it must look like a real phone number
        phone = postData.get('phone_number', '').strip()
        if phone and not re.match(self.PHONE_REGEX, phone):
            errors['phone_number'] = 'Please enter a valid phone number!'

        if postData.get('gender') not in dict(User.GENDER_CHOICES):
            errors['gender'] = 'Please select a gender!'

        if postData.get('country') not in dict(User.COUNTRY_CHOICES):
            errors['country'] = 'Please select your country!'

        dob_error = self._validate_dob(postData.get('date_of_birth', ''))
        if dob_error:
            errors['date_of_birth'] = dob_error

        bio = postData.get('bio', '')
        if len(bio) > 1000:
            errors['bio'] = 'Bio must be under 1000 characters!'

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
                except (UnidentifiedImageError, Exception):
                    errors['profile_pic'] = 'Uploaded file is not a valid image!'
                finally:
                    profile_pic.seek(0)
        return errors

    # Updates and saves user profile text fields and uploaded profile picture
    def update_profile(self, user, postData, files):
        user.first_name = postData.get('first_name', user.first_name).strip()
        user.last_name = postData.get('last_name', user.last_name).strip()
        user.email = postData.get('email', user.email).strip()
        user.username = postData.get('username', user.username).strip()
        user.phone_number = postData.get('phone_number', user.phone_number).strip()
        user.gender = postData.get('gender', user.gender)
        user.country = postData.get('country', user.country)
        dob_str = postData.get('date_of_birth')
        user.date_of_birth = date.fromisoformat(dob_str) if dob_str else user.date_of_birth
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
    # Added so the "Phone number" field in the profile form has somewhere to save to.
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Note: 'password' field is automatically provided by AbstractBaseUser, no manual field needed

    # Custom profile and demographic fields
       # Made nullable so a brand-new Google sign-up can be saved to the DB
    # immediately (Google never provides date of birth, gender, or
    # nationality), and the user fills these in afterward on the
    # lifestyle quiz / profile completion step.
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)

    # Tracks how the account was created. Used to:
    # - decide whether to show "Change password" vs "Add password" on the
    #   Security tab (Google users don't have a usable password by default)
    # - know whether profile completion (DOB/gender/country) is still pending
    AUTH_PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
    ]
    auth_provider = models.CharField(max_length=10, choices=AUTH_PROVIDER_CHOICES, default='email')
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    # Mandatory operational flags required for Django's admin panel access
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Set by an admin when banning (is_active=False) so other staff can see
    # why -- cleared again on unban so a future ban starts with a clean note.
    ban_reason = models.TextField(blank=True, null=True)

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

    # Property method to calculate the current age dynamically.
    # Returns None instead of crashing if date_of_birth hasn't been set yet
    # (e.g. a brand-new Google sign-up that hasn't completed the lifestyle
    # quiz / profile completion step).
    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return User.objects._calculate_age(self.date_of_birth)

    # True once the user has filled in the fields Google never provides.
    # Used to decide whether to redirect a freshly-logged-in user to the
    # "complete your profile" / lifestyle quiz step.
    @property
    def is_profile_complete(self):
        return bool(self.date_of_birth and self.gender and self.country)
    
    @property
    def birthday_this_year(self):
        today = date.today()
        dob = self.date_of_birth
        try:
            return dob.replace(year=today.year)
        except ValueError:
            # Feb 29 on a non-leap year → use Mar 1
            return date(today.year, 3, 1)

    @property
    def days_until_birthday(self):
        today = date.today()
        birthday = self.birthday_this_year
        if birthday < today:
            birthday = birthday.replace(year=today.year + 1)
        return (birthday - today).days

    @property
    def is_birthday_today(self):
        today = date.today()
        return (self.date_of_birth.month, self.date_of_birth.day) == (today.month, today.day)
    
        
    @property
    def is_id_verified(self):
        return self.verification_documents.filter(
            document_type='id_document', status='approved'
        ).exists()

    @property
    def is_rental_contract_verified(self):
        return self.verification_documents.filter(
            document_type='rental_contract', status='approved'
        ).exists()

    @property
    def verification_status(self):
        """e.g. {'id_document': 'approved', 'rental_contract': 'not_submitted'} — handy for templates."""
        docs = {d.document_type: d.status for d in self.verification_documents.all()}
        return {
            'id_document': docs.get('id_document', 'not_submitted'),
            'rental_contract': docs.get('rental_contract', 'not_submitted'),
        }


class LifestyleProfileManager(models.Manager):
    """
    Custom manager for LifestyleProfile, following the same
    "validator + create/update" pattern used by UserManager above,
    so the rest of the codebase stays consistent.
    """

    def lifestyle_validator(self, postData):
        """
        Validates the lifestyle profile form (all the option-card groups
        on the front end). Returns a dict of field -> error message.
        """
        errors = {}

        required_choice_fields = {
            'sleep_time': LifestyleProfile.SLEEP_TIME_CHOICES,
            'noise_level': LifestyleProfile.NOISE_LEVEL_CHOICES,
            'cleanliness': LifestyleProfile.CLEANLINESS_CHOICES,
            'social_type': LifestyleProfile.SOCIAL_TYPE_CHOICES,
            'preferred_roommates': LifestyleProfile.PREFERRED_ROOMMATES_CHOICES,
            'smoking': LifestyleProfile.SMOKING_CHOICES,
            # --- Extended preferences: required so every seeker has full
            # signal for compatibility_app's Gemini scoring ---
            'roommate_gender_pref': LifestyleProfile.ROOMMATE_GENDER_PREF_CHOICES,
            'dietary': LifestyleProfile.DIETARY_CHOICES,
            'guest_tolerance': LifestyleProfile.GUEST_TOLERANCE_CHOICES,
            'tenant_type': LifestyleProfile.TENANT_TYPE_CHOICES,
            'household_lang_pref': LifestyleProfile.HOUSEHOLD_LANG_PREF_CHOICES,
            'listing_type_pref': LifestyleProfile.LISTING_TYPE_PREF_CHOICES,
        }
        for field_name, choices in required_choice_fields.items():
            value = postData.get(field_name)
            if value not in dict(choices):
                errors[field_name] = 'Please select an option!'

        # wake_time is optional but if present must be one of the valid choices
        wake_time = postData.get('wake_time')
        if wake_time and wake_time not in dict(LifestyleProfile.WAKE_TIME_CHOICES):
            errors['wake_time'] = 'Invalid wake-up time option!'

        # religion and field are optional (nullable in the schema)
        religion = postData.get('religion')
        if religion and religion not in dict(LifestyleProfile.RELIGION_CHOICES):
            errors['religion'] = 'Invalid religion option!'

        field_of_study = postData.get('field')
        if field_of_study and field_of_study not in dict(LifestyleProfile.FIELD_CHOICES):
            errors['field'] = 'Invalid field of study/work option!'

        # min_stay_pref choices use int keys, but POST data always arrives as a string
        min_stay_pref = postData.get('min_stay_pref')
        if min_stay_pref in (None, ''):
            errors['min_stay_pref'] = 'Please select an option!'
        else:
            try:
                if int(min_stay_pref) not in dict(LifestyleProfile.MIN_STAY_PREF_CHOICES):
                    raise ValueError
            except ValueError:
                errors['min_stay_pref'] = 'Invalid option!'

        for field_name in ('budget_min', 'budget_max'):
            value = postData.get(field_name)
            if not value:
                errors[field_name] = 'Required!'
                continue
            try:
                if int(value) < 0:
                    raise ValueError
            except ValueError:
                errors[field_name] = 'Must be a positive whole number!'

        budget_min = postData.get('budget_min')
        budget_max = postData.get('budget_max')
        if budget_min and budget_max:
            try:
                if int(budget_min) > int(budget_max):
                    errors['budget_max'] = 'Max budget must be greater than or equal to min budget!'
            except ValueError:
                pass

        # Required booleans: must be explicitly "true"/"false", not absent.
        for field_name in ('alcohol_ok', 'works_from_home', 'wants_furnished', 'wants_building_amenities'):
            if postData.get(field_name) not in ('true', 'false'):
                errors[field_name] = 'Please select an option!'

        return errors

    def save_for_user(self, user, postData):
        """
        Creates or updates the LifestyleProfile row for this user
        (update_or_create keeps this idempotent: one row per user,
        matching the UNIQUE user_id constraint in the SQL schema).
        """
        defaults = {
            'sleep_time': postData.get('sleep_time'),
            'wake_time': postData.get('wake_time') or None,
            'noise_level': postData.get('noise_level'),
            'cleanliness': postData.get('cleanliness'),
            # Checkbox-style booleans: present in POST data means "checked"/true
            'cooking': postData.get('cooking') == 'true',
            'pets': postData.get('pets') == 'true',
            'smoking': postData.get('smoking'),
            'social_type': postData.get('social_type'),
            'preferred_roommates': postData.get('preferred_roommates'),
            'religion': postData.get('religion') or None,
            'field': postData.get('field') or None,
            # --- Extended preferences (required) ---
            'roommate_gender_pref': postData.get('roommate_gender_pref'),
            'budget_min': int(postData['budget_min']),
            'budget_max': int(postData['budget_max']),
            'dietary': postData.get('dietary'),
            'guest_tolerance': postData.get('guest_tolerance'),
            'tenant_type': postData.get('tenant_type'),
            'household_lang_pref': postData.get('household_lang_pref'),
            'alcohol_ok': postData.get('alcohol_ok') == 'true',
            'min_stay_pref': int(postData['min_stay_pref']),
            'listing_type_pref': postData.get('listing_type_pref'),
            'works_from_home': postData.get('works_from_home') == 'true',
            'wants_furnished': postData.get('wants_furnished') == 'true',
            'wants_building_amenities': postData.get('wants_building_amenities') == 'true',
        }
        profile, _created = self.update_or_create(user=user, defaults=defaults)
        return profile


class LifestyleProfile(models.Model):
    """
    One-to-one lifestyle/compatibility profile per user.
    Core fields mirror the original `lifestyle_profile` SQL table / ERD:
    sleep_time, noise_level, cleanliness, cooking, pets, smoking,
    social_type, preferred_roommates, religion, field,
    created_at, updated_at, user_id (FK, one-to-one, UNIQUE).

    Extended preference fields (roommate_gender_pref, budget_min/max, dietary,
    guest_tolerance, tenant_type, household_lang_pref, alcohol_ok, min_stay_pref,
    listing_type_pref, works_from_home, wants_furnished, wants_building_amenities)
    give seeker-side counterparts to more Listing house-rule groups. Required
    (not nullable): compatibility_app's Gemini scoring needs full signal for
    every seeker, not a partially-filled profile.
    """

    # --- Choice sets (kept identical to the ENUM values in the SQL schema) ---
    SLEEP_TIME_CHOICES = [
        ('early', 'Before 10PM'),
        ('normal', '10PM–12AM'),
        ('late', 'After 12AM'),
    ]
    WAKE_TIME_CHOICES = [
        ('early', 'Before 7AM'),
        ('normal', '7AM–9AM'),
        ('late', 'After 9AM'),
    ]
    NOISE_LEVEL_CHOICES = [
        ('quiet', 'Quiet'),
        ('moderate', 'Moderate'),
        ('noisy', 'Noisy'),
    ]
    CLEANLINESS_CHOICES = [
        ('very_clean', 'Very clean'),
        ('clean', 'Clean'),
        ('relaxed', 'Relaxed'),
    ]
    SOCIAL_TYPE_CHOICES = [
        ('private', 'Introvert'),
        ('moderate', 'Balanced'),
        ('social', 'Extrovert'),
    ]
    PREFERRED_ROOMMATES_CHOICES = [
        ('1', '1 roommate'),
        ('2', '2 roommates'),
        ('3', '3 roommates'),
        ('4+', '4+ roommates'),
    ]
    RELIGION_CHOICES = [
        ('muslim_committed', 'Muslim (practicing)'),
        ('muslim_not_committed', 'Muslim (non-practicing)'),
        ('christian', 'Christian'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    FIELD_CHOICES = [
        ('engineering', 'Engineering'),
        ('medicine', 'Medicine'),
        ('law', 'Law'),
        ('business', 'Business'),
        ('computer_science', 'Computer Science'),
        ('arts', 'Arts'),
        ('education', 'Education'),
        ('architecture', 'Architecture'),
        ('pharmacy', 'Pharmacy'),
        ('nursing', 'Nursing'),
        ('other', 'Other'),
    ]
    SMOKING_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('outside_only', 'Outside only'),
    ]

    # --- Extended preference choice sets (mirror the equivalent Listing field groups) ---
    ROOMMATE_GENDER_PREF_CHOICES = [
        ('males_only', 'Males only'),
        ('females_only', 'Females only'),
        ('any', 'No preference'),
    ]
    DIETARY_CHOICES = [
        ('none', 'No restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('halal', 'Halal only'),
        ('no_seafood', 'No seafood'),
    ]
    GUEST_TOLERANCE_CHOICES = [
        ('strict', 'Prefers few/no guests'),
        ('moderate', 'Occasional guests OK'),
        ('relaxed', 'Frequent guests OK'),
    ]
    TENANT_TYPE_CHOICES = [
        ('students', 'Student'),
        ('professionals', 'Working professional'),
        ('families', 'Family'),
        ('anyone', 'Other'),
    ]
    HOUSEHOLD_LANG_PREF_CHOICES = [
        ('english', 'English-speaking household'),
        ('arabic', 'Arabic-only household'),
        ('local', 'Locals preferred'),
        ('mixed', 'Mixed nationalities'),
        ('no_preference', 'No preference'),
    ]
    MIN_STAY_PREF_CHOICES = [
        (1, '1 Month'),
        (2, '2 Months'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '1 Year'),
        (0, 'Flexible'),
    ]
    LISTING_TYPE_PREF_CHOICES = [
        ('private_room', 'Private Room'),
        ('full_apartment', 'Full Apartment'),
        ('shared_bed', 'Shared Bed'),
        ('roommate_wanted', 'Roommate Wanted'),
    ]

    # One-to-one: every user has at most one lifestyle profile row.
    # related_name lets us access this from the User side as `user.lifestyle_profile`.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='lifestyle_profile',
    )

    # --- Sleep & schedule ---
    sleep_time = models.CharField(max_length=10, choices=SLEEP_TIME_CHOICES)
    wake_time = models.CharField(max_length=10, choices=WAKE_TIME_CHOICES, blank=True, null=True)

    # --- Noise & social ---
    noise_level = models.CharField(max_length=10, choices=NOISE_LEVEL_CHOICES)
    social_type = models.CharField(max_length=10, choices=SOCIAL_TYPE_CHOICES)

    # --- Cleanliness & habits ---
    cleanliness = models.CharField(max_length=12, choices=CLEANLINESS_CHOICES)
    # Stored as booleans to match the SQL TINYINT(1) flags.
    cooking = models.BooleanField(default=False)
    pets = models.BooleanField(default=False)
    # Smoking has 3 real-world states ("outside only" matters a lot to roommates),
    # so we store it as a small CharField rather than a plain boolean.
    smoking = models.CharField(max_length=12, choices=SMOKING_CHOICES, default='no')

    # --- Roommate preference ---
    preferred_roommates = models.CharField(max_length=2, choices=PREFERRED_ROOMMATES_CHOICES)

    # --- Religion & field of study/work (nullable: sensitive / optional info) ---
    religion = models.CharField(max_length=25, choices=RELIGION_CHOICES, blank=True, null=True)
    field = models.CharField(max_length=20, choices=FIELD_CHOICES, blank=True, null=True)

    # --- Extended preferences (required) ---
    roommate_gender_pref = models.CharField(max_length=15, choices=ROOMMATE_GENDER_PREF_CHOICES)
    budget_min = models.PositiveIntegerField()
    budget_max = models.PositiveIntegerField()
    dietary = models.CharField(max_length=15, choices=DIETARY_CHOICES)
    guest_tolerance = models.CharField(max_length=10, choices=GUEST_TOLERANCE_CHOICES)
    tenant_type = models.CharField(max_length=15, choices=TENANT_TYPE_CHOICES)
    household_lang_pref = models.CharField(max_length=15, choices=HOUSEHOLD_LANG_PREF_CHOICES)
    alcohol_ok = models.BooleanField()
    min_stay_pref = models.PositiveSmallIntegerField(choices=MIN_STAY_PREF_CHOICES)
    listing_type_pref = models.CharField(max_length=20, choices=LISTING_TYPE_PREF_CHOICES)
    works_from_home = models.BooleanField()
    wants_furnished = models.BooleanField()
    wants_building_amenities = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager: handles validation + create-or-update logic
    objects = LifestyleProfileManager()

    # Every field the questionnaire can collect, used to compute a granular
    # completeness score (see `completeness_fraction`). Only wake_time,
    # religion, and field remain genuinely optional — everything else is
    # required at save time (see lifestyle_validator), so a saved profile
    # is always at/near full completeness.
    ALL_PREFERENCE_FIELDS = [
        'sleep_time', 'wake_time', 'noise_level', 'cleanliness', 'smoking',
        'social_type', 'preferred_roommates', 'religion', 'field',
        'roommate_gender_pref', 'budget_min', 'budget_max', 'dietary',
        'guest_tolerance', 'tenant_type', 'household_lang_pref', 'alcohol_ok',
        'min_stay_pref', 'listing_type_pref', 'works_from_home',
        'wants_furnished', 'wants_building_amenities',
    ]

    class Meta:
        db_table = 'lifestyle_profile'  # keep the exact table name from the original SQL

    def __str__(self):
        return f'Lifestyle profile of {self.user.username}'

    @property
    def fields_filled_count(self):
        """How many of ALL_PREFERENCE_FIELDS have a real (non-None/non-empty) value."""
        count = 0
        for field_name in self.ALL_PREFERENCE_FIELDS:
            value = getattr(self, field_name)
            if value is not None and value != '':
                count += 1
        return count

    @property
    def completeness_fraction(self):
        """0.0-1.0 fraction of ALL_PREFERENCE_FIELDS that are filled in."""
        return self.fields_filled_count / len(self.ALL_PREFERENCE_FIELDS)


class Testimonial(models.Model):
    ROOM_SEEKER = 'seeker'
    ROOM_POSTER = 'poster'
    ROLE_CHOICES = [
        (ROOM_SEEKER, 'Room Seeker'),
        (ROOM_POSTER, 'Room Poster'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='testimonials',
    )
    reviewer_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    location = models.CharField(max_length=120, blank=True)
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core_app'
        db_table = 'core_app_testimonial'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reviewer_name} — {self.get_role_display()}'

    @property
    def reviewer_initials(self):
        parts = self.reviewer_name.strip().split()
        if len(parts) == 0:
            return ''
        if len(parts) == 1:
            return parts[0][:2].upper()
        return ''.join(part[0].upper() for part in parts[:2])


class OTPCode(models.Model):
    """
    Stores a one-time password (OTP) for password reset.
    Each user can have multiple OTP records, but only the latest unused
    and non-expired one is considered valid during verification.
    """
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code       = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.user.email} — {self.code}'

    @property
    def is_expired(self):
        """Returns True if the OTP was created more than 2 minutes ago."""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=2)

    @classmethod
    def generate_for_user(cls, user):
        """
        Marks all previous unused OTPs for this user as used,
        then creates and returns a fresh 4-digit OTP.
        Ensures only one active OTP exists per user at a time.
        """
        # Invalidate any previous unused codes
        cls.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate a new 4-digit code (zero-padded: 0000–9999)
        code = str(random.randint(0, 9999)).zfill(4)
        return cls.objects.create(user=user, code=code)
    

def verification_document_path(instance, filename):
    """
    Builds an unguessable upload path: verification_docs/user_<id>/<doc_type>/<uuid>.<ext>
    A UUID filename (instead of the original filename) means nobody can find or
    guess another user's document path even if they somehow saw a sibling URL.
    """
    ext = Path(filename).suffix.lower()
    unique_name = f'{uuid.uuid4().hex}{ext}'
    if instance.document_type == 'rental_contract' and instance.listing_id:
        return f'verification_docs/user_{instance.user_id}/rental_contract/listing_{instance.listing_id}/{unique_name}'
    return f'verification_docs/user_{instance.user_id}/{instance.document_type}/{unique_name}'

class VerificationDocumentManager(models.Manager):
    """
    Same validator + create/update pattern as LifestyleProfileManager above,
    so this stays consistent with the rest of the codebase.
    """

    ALLOWED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')
    MAX_SIZE_BYTES = 8 * 1024 * 1024  # 8MB — contracts can be multi-page scans

    def validate_upload(self, file):
        """Returns an error string, or None if the uploaded file is valid."""
        if file.size > self.MAX_SIZE_BYTES:
            return 'File must be smaller than 8MB!'
        ext = Path(file.name).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return 'File must be a PDF, JPG, or PNG!'
        return None

    def submit_document(self, user, document_type, file, listing=None):
        """
        Creates a new document row, or overwrites + resets to 'pending' if the
        user already submitted this document_type before (e.g. resubmitting
        after a rejection). One row per (user, document_type) — see Meta below.
        """
        lookup = {'user': user, 'document_type': document_type}
        if document_type == VerificationDocument.RENTAL_CONTRACT:
            if listing is None:
                raise ValueError('A listing is required for rental_contract documents.')
            lookup['listing'] = listing
        doc, _created = self.update_or_create(
            **lookup,
            defaults={
                'file': file,
                'status': VerificationDocument.PENDING,
                'rejection_reason': '',
                'reviewed_by': None,
                'reviewed_at': None,
            },
        )
        return doc

class VerificationDocument(models.Model):
    ID_DOCUMENT = 'id_document'
    RENTAL_CONTRACT = 'rental_contract'
    DOCUMENT_TYPE_CHOICES = [
        (ID_DOCUMENT, 'ID Document'),
        (RENTAL_CONTRACT, 'Rental Contract'),
    ]

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='verification_documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)

    # Only set for RENTAL_CONTRACT — each listing has its own contract,
    # since a landlord with 3 rooms doesn't share one contract across all.
    # Stays null for ID_DOCUMENT (that's one-per-user, not one-per-listing).
    listing = models.ForeignKey(
        'listings_app.Listing', on_delete=models.CASCADE, null=True, blank=True,
        related_name='contract_documents',
    )

    file = models.FileField(upload_to=verification_document_path)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    rejection_reason = models.TextField(blank=True)

    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_documents', limit_choices_to={'is_staff': True},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = VerificationDocumentManager()

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            # id_document: one per user (listing stays null)
            models.UniqueConstraint(
                fields=['user', 'document_type'],
                condition=models.Q(document_type='id_document'),
                name='unique_id_document_per_user',
            ),
            # rental_contract: one per listing (not per user!)
            models.UniqueConstraint(
                fields=['listing', 'document_type'],
                condition=models.Q(document_type='rental_contract'),
                name='unique_rental_contract_per_listing',
            ),
        ]