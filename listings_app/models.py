import json
from datetime import date, time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


_VALID_LISTING_TYPES = {'private_room', 'full_apartment', 'shared_bed', 'roommate_wanted'}
_VALID_TENANT_TYPES  = {'students', 'professionals', 'families', 'anyone'}
_VALID_MIN_STAY      = {0, 1, 2, 3, 6, 12}
_MAX_OCCUPANTS = {
    'private_room':    5,
    'full_apartment':  20,
    'shared_bed':      2,
    'roommate_wanted': 1,
}

_BOOL_FIELDS = [
    'no_smoking', 'smoking_outside_ok', 'no_alcohol', 'no_vaping',
    'muslims_only', 'christians_only', 'all_religions_ok', 'halal_kitchen', 'prayer_space',
    'males_only', 'females_only', 'students_only', 'professionals_only', 'expats_welcome', 'no_children',
    'pets_allowed', 'dogs_allowed', 'cats_allowed', 'no_pets',
    'must_cook', 'vegetarian_house', 'no_seafood', 'shared_groceries', 'equipped_kitchen', 'no_food_in_rooms',
    'quiet_after_10', 'early_sleepers', 'no_loud_music', 'no_parties', 'calm_environment', 'no_calls_common',
    'shared_cleaning', 'no_shoes_inside', 'respect_spaces', 'clean_bathroom', 'separate_recycling',
    'no_overnight_guests', 'guests_with_notice', 'curfew_midnight', 'no_gatherings',
    'fully_furnished', 'en_suite_bathroom', 'air_conditioning', 'heating', 'hot_water_24_7',
    'natural_light', 'balcony', 'storage_space', 'tv_common_area', 'elevator',
    'electricity_included', 'water_included', 'gas_included', 'wifi_included', 'waste_included', 'bills_split_equally',
    'study_desk', 'quiet_work_env', 'multiple_outlets', 'printer_access',
    'swimming_pool', 'gym_access', 'rooftop_access', 'garden', 'common_lounge', 'sauna',
    'security_guard', 'cctv', 'gated_building', 'private_lock', 'smart_lock', 'intercom',
    'private_parking', 'shared_parking', 'near_metro', 'bus_stop_nearby', 'bike_storage',
    'washing_machine', 'dryer', 'ironing_board', 'clothesline',
    'security_deposit', 'rent_negotiable', 'monthly_payment', 'quarterly_payment', 'online_payment',
    'english_household', 'arabic_only', 'local_preferred', 'mixed_nationalities',
    'smoke_alarm', 'carbon_monoxide_alarm', 'first_aid_kit',
]


# ── Manager ───────────────────────────────────────────────────────────────────

class ListingManager(models.Manager):

    def listing_validator(self, post_data, files=None):
        """
        Validate raw POST data and FILES.
        Returns an errors dict  {field: [msg, ...]}  — empty dict means valid.
        Does NOT raise and does NOT touch the database.
        """
        errors = {}

        def flag(name):
            return name in post_data or post_data.get(name) in ('on', '1', 'true')

        # ── Step 1 ────────────────────────────────────────────────────────────

        listing_type = post_data.get('listing_type', '').strip()
        if listing_type not in _VALID_LISTING_TYPES:
            errors['listing_type'] = ['Please select a valid listing type.']

        tenant_raw = post_data.get('tenant_types', 'anyone').strip()
        if tenant_raw != 'anyone':
            tenant_types = [t.strip() for t in tenant_raw.split(',') if t.strip()]
            invalid = set(tenant_types) - _VALID_TENANT_TYPES
            if invalid:
                errors['tenant_types'] = [f'Invalid tenant type(s): {", ".join(invalid)}.']
            elif not tenant_types:
                errors['tenant_types'] = ['Please select at least one tenant type.']

        try:
            price = float(post_data.get('price', '') or 0)
            if price <= 0:
                raise ValueError
        except ValueError:
            errors['price'] = ['Price is required and must be greater than 0.']

        try:
            max_occupants = int(post_data.get('max_occupants', 1) or 1)
            if max_occupants < 1:
                raise ValueError
            cap = _MAX_OCCUPANTS.get(listing_type, 20)
            if max_occupants > cap:
                errors['max_occupants'] = [
                    f'Max occupants for "{listing_type}" cannot exceed {cap}.'
                ]
        except ValueError:
            errors['max_occupants'] = ['Max occupants must be a positive integer.']

        try:
            min_stay = int(post_data.get('min_stay_months', 3) or 3)
            if min_stay not in _VALID_MIN_STAY:
                raise ValueError
        except ValueError:
            errors['min_stay_months'] = ['Please select a valid minimum stay duration.']

        # ── Step 2 ────────────────────────────────────────────────────────────

        title = post_data.get('title', '').strip()
        if not title:
            errors['title'] = ['A listing title is required.']
        elif len(title) < 10:
            errors['title'] = ['Title must be at least 10 characters.']

        lat_raw = post_data.get('lat', '').strip()
        lng_raw = post_data.get('lng', '').strip()
        if lat_raw or lng_raw:
            try:
                lat = float(lat_raw) if lat_raw else None
                lng = float(lng_raw) if lng_raw else None
                if lat is not None and not (-90 <= lat <= 90):
                    raise ValueError
                if lng is not None and not (-180 <= lng <= 180):
                    raise ValueError
            except ValueError:
                errors['location'] = ['Invalid map coordinates.']

        # ── Step 3 ────────────────────────────────────────────────────────────

        description = post_data.get('description', '').strip()
        if len(description) > 5000:
            errors['description'] = ['Description cannot exceed 5000 characters.']

        # ── Step 4 — cross-field conflicts ────────────────────────────────────

        if flag('no_smoking') and flag('smoking_outside_ok'):
            errors['smoking'] = ['"No Smoking" and "Smoking Outside OK" cannot both be on.']
        if flag('pets_allowed') and flag('no_pets'):
            errors['pets'] = ['"Pets Allowed" and "No Pets" cannot both be on.']
        if flag('males_only') and flag('females_only'):
            errors['gender'] = ['"Males Only" and "Females Only" cannot both be on.']
        if flag('muslims_only') and flag('christians_only'):
            errors['religion'] = ['"Muslims Only" and "Christians Only" cannot both be on.']

        # ── Images ────────────────────────────────────────────────────────────

        if files:
            _allowed = {'image/jpeg', 'image/png', 'image/webp'}
            for img in files.getlist('images')[:10]:
                if img.size > 10 * 1024 * 1024:
                    errors.setdefault('images', []).append(
                        f'"{img.name}" exceeds the 10 MB limit.'
                    )
                elif img.content_type not in _allowed:
                    errors.setdefault('images', []).append(
                        f'"{img.name}" is not a supported type (JPEG, PNG, WEBP).'
                    )

        return errors

    def _extract_fields(self, post_data):
        """
        Parse raw POST data into a dict of Listing field values (everything
        except `poster` and `status`). Shared by create_from_post and
        update_from_post — does NOT validate and does NOT touch the database.
        """
        def flag(name):
            return name in post_data or post_data.get(name) in ('on', '1', 'true')

        # ── Step 1 ────────────────────────────────────────────────────────────

        listing_type = post_data.get('listing_type', 'private_room').strip()

        tenant_raw = post_data.get('tenant_types', 'anyone').strip()
        tenant_types = (
            ['anyone'] if tenant_raw == 'anyone'
            else [t.strip() for t in tenant_raw.split(',') if t.strip()] or ['anyone']
        )

        price = float(post_data.get('price', 0) or 0)

        try:
            available_from = date.fromisoformat(post_data.get('available_from', ''))
        except (ValueError, TypeError):
            available_from = date.today()

        max_occupants   = max(1, int(post_data.get('max_occupants', 1) or 1))
        min_stay_months = int(post_data.get('min_stay_months', 3) or 3)

        # ── Step 2 ────────────────────────────────────────────────────────────

        title    = post_data.get('title',    '').strip()[:80]
        country  = post_data.get('country',  '').strip()
        city     = post_data.get('city',     '').strip()
        district = post_data.get('district', '').strip()
        street   = post_data.get('street',   '').strip()
        address  = post_data.get('address',  '').strip()
        landmark = post_data.get('landmark', '').strip()

        lat = float(post_data['lat']) if post_data.get('lat') else None
        lng = float(post_data['lng']) if post_data.get('lng') else None

        # ── Step 3 ────────────────────────────────────────────────────────────

        description  = post_data.get('description', '').strip()[:5000]
        ai_generated = post_data.get('ai_generated') == '1'
        notes        = post_data.get('notes', '').strip()

        # ── Step 4 booleans ───────────────────────────────────────────────────

        bool_fields = {name: flag(name) for name in _BOOL_FIELDS}

        try:
            check_in_time = time.fromisoformat(post_data.get('check_in_time', '')) if post_data.get('check_in_time') else None
        except ValueError:
            check_in_time = None
        try:
            check_out_time = time.fromisoformat(post_data.get('check_out_time', '')) if post_data.get('check_out_time') else None
        except ValueError:
            check_out_time = None

        # ── Custom requirements ───────────────────────────────────────────────

        try:
            raw = json.loads(post_data.get('custom_requirements', '[]') or '[]')
            if not isinstance(raw, list):
                raise ValueError
            custom_requirements = [
                {'text': item['text'].strip()[:200], 'enabled': bool(item.get('enabled', True))}
                for item in raw[:20]
                if isinstance(item, dict) and isinstance(item.get('text', ''), str)
            ]
        except (json.JSONDecodeError, ValueError, TypeError):
            custom_requirements = []

        return {
            'listing_type': listing_type,
            'tenant_types': tenant_types,
            'price': price,
            'available_from': available_from,
            'max_occupants': max_occupants,
            'min_stay_months': min_stay_months,
            'title': title,
            'country': country,
            'city': city,
            'district': district,
            'street': street,
            'address': address,
            'landmark': landmark,
            'lat': lat,
            'lng': lng,
            'description': description,
            'ai_generated': ai_generated,
            'notes': notes,
            'custom_requirements': custom_requirements,
            'check_in_time': check_in_time,
            'check_out_time': check_out_time,
            **bool_fields,
        }

    def _save_new_images(self, listing, files, post_data, order=0):
        """Create ListingImage rows from uploaded files, starting at `order`. Returns the next free order."""
        if not files:
            return order
        _allowed = {'image/jpeg', 'image/png', 'image/webp'}
        _valid_labels = {c for c, _ in ListingImage.ROOM_LABEL_CHOICES}
        raw_labels = post_data.get('image_labels', '').split(',')
        for i, img in enumerate(files.getlist('images')[:10]):
            if img.size > 10 * 1024 * 1024 or img.content_type not in _allowed:
                continue
            label = raw_labels[i].strip() if i < len(raw_labels) else ''
            if label not in _valid_labels:
                label = 'other'
            ListingImage.objects.create(listing=listing, image=img, room_label=label, order=order)
            order += 1
        return order

    def create_from_post(self, post_data, files, poster):
        """
        Validate, then create and return a Listing from raw POST data.
        Raises ValidationError({field: [msg]}) if validation fails.
        """
        errors = self.listing_validator(post_data, files)
        if errors:
            raise ValidationError(errors)

        fields = self._extract_fields(post_data)
        status = 'active' if post_data.get('action') == 'publish' else 'draft'

        listing = self.create(poster=poster, status=status, **fields)

        self._save_new_images(listing, files, post_data)

        return listing

    def update_from_post(self, listing, post_data, files, kept_images_json='[]'):
        """
        Validate, then update `listing` in place from raw POST data.
        Raises ValidationError({field: [msg]}) if validation fails.

        kept_images_json: JSON string of [{"id": <ListingImage.pk>, "label": <str>,
        "order": <int>}, ...] for existing images to keep (with possibly-updated
        label/order). Existing images NOT listed are deleted. New files in
        files.getlist('images') are appended after the kept ones.
        """
        errors = self.listing_validator(post_data, files)
        if errors:
            raise ValidationError(errors)

        fields = self._extract_fields(post_data)
        status = 'active' if post_data.get('action') == 'publish' else 'draft'

        for field, value in fields.items():
            setattr(listing, field, value)
        listing.status = status
        listing.save()

        # ── Reconcile existing images ────────────────────────────────────────
        try:
            kept = json.loads(kept_images_json or '[]')
            if not isinstance(kept, list):
                kept = []
        except (json.JSONDecodeError, ValueError, TypeError):
            kept = []

        kept_by_id = {
            int(item['id']): item
            for item in kept
            if isinstance(item, dict) and str(item.get('id', '')).isdigit()
        }

        _valid_labels = {c for c, _ in ListingImage.ROOM_LABEL_CHOICES}
        order = 0
        for img in listing.images.all():
            if img.pk in kept_by_id:
                label = kept_by_id[img.pk].get('label', img.room_label)
                img.room_label = label if label in _valid_labels else img.room_label
                img.order = order
                img.save(update_fields=['room_label', 'order'])
                order += 1
            else:
                img.delete()

        self._save_new_images(listing, files, post_data, order=order)

        return listing


# ── Models ────────────────────────────────────────────────────────────────────

class Listing(models.Model):

    # ── Step 1: Basic Info ────────────────────────────────────────────────────

    LISTING_TYPE_CHOICES = [
        ('private_room',    'Private Room'),
        ('full_apartment',  'Full Apartment'),
        ('shared_bed',      'Shared Bed'),
        ('roommate_wanted', 'Roommate Wanted'),
    ]
    TENANT_TYPE_CHOICES = [
        ('students',      'Students'),
        ('professionals', 'Working Professionals'),
        ('families',      'Families'),
        ('anyone',        'Anyone Welcome'),
    ]
    MIN_STAY_CHOICES = [
        (1,  '1 Month'),
        (2,  '2 Months'),
        (3,  '3 Months'),
        (6,  '6 Months'),
        (12, '1 Year'),
        (0,  'Flexible'),
    ]

    poster          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    listing_type    = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='private_room')
    tenant_types    = models.JSONField(default=list, blank=True)
    price           = models.DecimalField(max_digits=8, decimal_places=2)
    available_from  = models.DateField(default=date.today)
    max_occupants   = models.PositiveSmallIntegerField(default=1)
    min_stay_months = models.PositiveSmallIntegerField(choices=MIN_STAY_CHOICES, default=3)

    # ── Step 2: Title & Location ──────────────────────────────────────────────

    title    = models.CharField(max_length=80)
    country  = models.CharField(max_length=100, blank=True)
    city     = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    street   = models.CharField(max_length=200, blank=True)
    address  = models.TextField(blank=True)
    landmark = models.CharField(max_length=200, blank=True)
    lat      = models.FloatField(null=True, blank=True)
    lng      = models.FloatField(null=True, blank=True)

    # ── Step 3: Photos & Description ─────────────────────────────────────────

    description  = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)
    notes        = models.TextField(blank=True)

    # ── Step 4: Smoking & Substances ─────────────────────────────────────────

    no_smoking         = models.BooleanField(default=False)
    smoking_outside_ok = models.BooleanField(default=False)
    no_alcohol         = models.BooleanField(default=False)
    no_vaping          = models.BooleanField(default=False)

    # ── Step 4: Religion & Culture ───────────────────────────────────────────

    muslims_only     = models.BooleanField(default=False)
    christians_only  = models.BooleanField(default=False)
    all_religions_ok = models.BooleanField(default=False)
    halal_kitchen    = models.BooleanField(default=False)
    prayer_space     = models.BooleanField(default=False)

    # ── Step 4: Gender & Tenant Type ─────────────────────────────────────────

    males_only         = models.BooleanField(default=False)
    females_only       = models.BooleanField(default=False)
    students_only      = models.BooleanField(default=False)
    professionals_only = models.BooleanField(default=False)
    expats_welcome     = models.BooleanField(default=False)
    no_children        = models.BooleanField(default=False)

    # ── Step 4: Pets & Animals ───────────────────────────────────────────────

    pets_allowed = models.BooleanField(default=False)
    dogs_allowed = models.BooleanField(default=False)
    cats_allowed = models.BooleanField(default=False)
    no_pets      = models.BooleanField(default=False)

    # ── Step 4: Kitchen & Food ───────────────────────────────────────────────

    must_cook        = models.BooleanField(default=False)
    vegetarian_house = models.BooleanField(default=False)
    no_seafood       = models.BooleanField(default=False)
    shared_groceries = models.BooleanField(default=False)
    equipped_kitchen = models.BooleanField(default=False)
    no_food_in_rooms = models.BooleanField(default=False)

    # ── Step 4: Noise & Schedule ─────────────────────────────────────────────

    quiet_after_10   = models.BooleanField(default=False)
    early_sleepers   = models.BooleanField(default=False)
    no_loud_music    = models.BooleanField(default=False)
    no_parties       = models.BooleanField(default=False)
    calm_environment = models.BooleanField(default=False)
    no_calls_common  = models.BooleanField(default=False)

    # ── Step 4: Cleanliness & Hygiene ────────────────────────────────────────

    shared_cleaning    = models.BooleanField(default=False)
    no_shoes_inside    = models.BooleanField(default=False)
    respect_spaces     = models.BooleanField(default=False)
    clean_bathroom     = models.BooleanField(default=False)
    separate_recycling = models.BooleanField(default=False)

    # ── Step 4: Guest Rules ───────────────────────────────────────────────────

    no_overnight_guests = models.BooleanField(default=False)
    guests_with_notice  = models.BooleanField(default=False)
    curfew_midnight     = models.BooleanField(default=False)
    no_gatherings       = models.BooleanField(default=False)

    # ── Step 4: Room Amenities ────────────────────────────────────────────────

    fully_furnished   = models.BooleanField(default=False)
    en_suite_bathroom = models.BooleanField(default=False)
    air_conditioning  = models.BooleanField(default=False)
    heating           = models.BooleanField(default=False)
    hot_water_24_7    = models.BooleanField(default=False)
    natural_light     = models.BooleanField(default=False)
    balcony           = models.BooleanField(default=False)
    storage_space     = models.BooleanField(default=False)
    tv_common_area    = models.BooleanField(default=False)
    elevator          = models.BooleanField(default=False)

    # ── Step 4: Bills & Utilities ─────────────────────────────────────────────

    electricity_included = models.BooleanField(default=False)
    water_included       = models.BooleanField(default=False)
    gas_included         = models.BooleanField(default=False)
    wifi_included        = models.BooleanField(default=False)
    waste_included       = models.BooleanField(default=False)
    bills_split_equally  = models.BooleanField(default=False)

    # ── Step 4: Work & Study Setup ────────────────────────────────────────────

    study_desk       = models.BooleanField(default=False)
    quiet_work_env   = models.BooleanField(default=False)
    multiple_outlets = models.BooleanField(default=False)
    printer_access   = models.BooleanField(default=False)

    # ── Step 4: Building Facilities ──────────────────────────────────────────

    swimming_pool  = models.BooleanField(default=False)
    gym_access     = models.BooleanField(default=False)
    rooftop_access = models.BooleanField(default=False)
    garden         = models.BooleanField(default=False)
    common_lounge  = models.BooleanField(default=False)
    sauna          = models.BooleanField(default=False)

    # ── Step 4: Security ──────────────────────────────────────────────────────

    security_guard = models.BooleanField(default=False)
    cctv           = models.BooleanField(default=False)
    gated_building = models.BooleanField(default=False)
    private_lock   = models.BooleanField(default=False)
    smart_lock     = models.BooleanField(default=False)
    intercom       = models.BooleanField(default=False)

    # ── Step 4: Parking & Transport ───────────────────────────────────────────

    private_parking = models.BooleanField(default=False)
    shared_parking  = models.BooleanField(default=False)
    near_metro      = models.BooleanField(default=False)
    bus_stop_nearby = models.BooleanField(default=False)
    bike_storage    = models.BooleanField(default=False)

    # ── Step 4: Laundry ───────────────────────────────────────────────────────

    washing_machine = models.BooleanField(default=False)
    dryer           = models.BooleanField(default=False)
    ironing_board   = models.BooleanField(default=False)
    clothesline     = models.BooleanField(default=False)

    # ── Step 4: Financial Terms ───────────────────────────────────────────────

    security_deposit  = models.BooleanField(default=False)
    rent_negotiable   = models.BooleanField(default=False)
    monthly_payment   = models.BooleanField(default=False)
    quarterly_payment = models.BooleanField(default=False)
    online_payment    = models.BooleanField(default=False)

    # ── Step 4: House Rules & Safety ─────────────────────────────────────────

    check_in_time         = models.TimeField(null=True, blank=True)
    check_out_time        = models.TimeField(null=True, blank=True)
    smoke_alarm            = models.BooleanField(default=False)
    carbon_monoxide_alarm  = models.BooleanField(default=False)
    first_aid_kit           = models.BooleanField(default=False)

    # ── Step 4: Language & Background ────────────────────────────────────────

    english_household   = models.BooleanField(default=False)
    arabic_only         = models.BooleanField(default=False)
    local_preferred     = models.BooleanField(default=False)
    mixed_nationalities = models.BooleanField(default=False)

    # ── Custom Requirements ───────────────────────────────────────────────────

    custom_requirements = models.JSONField(default=list, blank=True)

    # ── Meta ──────────────────────────────────────────────────────────────────

    STATUS_CHOICES = [
        ('draft',  'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'

    def __str__(self):
        return f'{self.title} — {self.get_listing_type_display()} ({self.city})'

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def custom_requirements_json(self):
        return json.dumps(self.custom_requirements)

class Favorite(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    listing    = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'listing')

    def __str__(self):
        return f'{self.user} ♥ {self.listing.title}'


class ListingImage(models.Model):
    ROOM_LABEL_CHOICES = [
        ('living_room', 'Living Room'),
        ('bedroom',     'Bedroom'),
        ('kitchen',     'Kitchen'),
        ('bathroom',    'Bathroom'),
        ('exterior',    'Exterior'),
        ('other',       'Additional Photos'),
    ]

    listing     = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image       = models.ImageField(upload_to='listings/%Y/%m/')
    room_label  = models.CharField(max_length=20, choices=ROOM_LABEL_CHOICES, default='other')
    order       = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Image {self.order} for {self.listing.title}'
