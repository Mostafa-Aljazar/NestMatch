import io
import random
import urllib.request

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from listings_app.models import Listing, ListingImage

User = get_user_model()

TITLES = [
    "Cozy Room Near Ain Shams University",
    "Spacious Flat Near AUC New Cairo",
    "Modern Studio in Heliopolis",
    "Bright Private Room in Zamalek",
    "Affordable Shared Room in Maadi",
    "Furnished Room Near Cairo University",
    "Quiet Room in Mohandessin",
    "Sunny Apartment in Dokki",
    "Room with Balcony in Nasr City",
    "Studio Near Future University",
    "Private Room in Rehab City",
    "Cozy Bed in New Cairo Compound",
    "Furnished Studio in Garden City",
    "Large Room Near Al-Azhar University",
    "Roommate Wanted in 6th of October",
    "Shared Flat in Madinaty",
    "Private Room in Shorouk City",
    "Modern Room in Fifth Settlement",
    "Room in Quiet Building in Agouza",
    "Affordable Room Near Metro Station",
]

CITIES = ["Cairo", "Giza", "Cairo", "Cairo", "Cairo", "Giza", "Cairo", "Giza", "Cairo", "Cairo"]

DISTRICTS = [
    "Nasr City", "New Cairo", "Heliopolis", "Zamalek", "Maadi",
    "Dokki", "Mohandessin", "6th of October", "Garden City", "Rehab City",
    "Fifth Settlement", "Shorouk", "Agouza", "Madinaty", "Shubra",
]

LISTING_TYPES = [
    "private_room", "private_room", "private_room",
    "full_apartment", "full_apartment",
    "shared_bed",
    "roommate_wanted", "roommate_wanted",
]

PRICES = [120, 150, 180, 200, 220, 250, 280, 300, 350, 400, 420, 450, 500, 550, 600]

ROOM_IMAGES = [
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=700&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=700&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=700&q=80",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=700&q=80",
    "https://images.unsplash.com/photo-1505693314120-0d443867891c?w=700&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=700&q=80",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=700&q=80",
    "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=700&q=80",
    "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=700&q=80",
    "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=700&q=80",
]

DESCRIPTIONS = [
    "A comfortable and well-lit room available in a shared apartment. The flat has a modern kitchen, high-speed WiFi, and a friendly atmosphere. Close to major universities and metro stations.",
    "Spacious private room in a quiet residential building. Air conditioning, hot water 24/7, and all bills included. Ideal for students or young professionals.",
    "Furnished studio in the heart of the city. No smoking allowed. Great natural light and a clean shared bathroom. 5 minutes walk to the metro.",
    "Bright apartment available for sharing. Fully equipped kitchen, fast internet, and a secure building with 24/7 guard. Flexible move-in date.",
    "Looking for a reliable roommate to share a modern 2-bedroom flat. We are clean, respectful, and mostly students. No pets please.",
    "Large private room with en-suite bathroom. Fully furnished with study desk. Bills included. Females only. Very quiet environment.",
    "Affordable shared room in a friendly household. Close to Al-Azhar and shopping centers. WiFi and electricity included in the price.",
    "Modern studio flat in a gated compound. Swimming pool and gym access. Private parking available. Perfect for working professionals.",
]


class Command(BaseCommand):
    help = "Seed 20 fake listings for development"

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete all existing listings first')

    def handle(self, *args, **options):
        if options['clear']:
            Listing.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all listings."))

        # get or create a poster user
        poster, created = User.objects.get_or_create(
            username='demo_poster',
            defaults={
                'email': 'poster@nestmatch.dev',
                'first_name': 'Demo',
                'last_name': 'Poster',
            }
        )
        if created:
            poster.set_password('nestmatch123')
            poster.save()
            self.stdout.write(f"Created user: demo_poster / nestmatch123")

        created_count = 0
        for i in range(20):
            ltype = random.choice(LISTING_TYPES)

            max_occ_cap = {'private_room': 5, 'full_apartment': 20, 'shared_bed': 2, 'roommate_wanted': 1}
            max_occ = random.randint(1, max_occ_cap[ltype])

            no_smoking   = random.random() > 0.4
            pets_allowed = random.random() > 0.5
            no_pets      = not pets_allowed
            males_only   = random.random() > 0.7
            females_only = (not males_only) and random.random() > 0.7

            listing = Listing.objects.create(
                poster          = poster,
                listing_type    = ltype,
                tenant_types    = random.choice([['anyone'], ['students'], ['professionals'], ['students', 'professionals']]),
                price           = random.choice(PRICES),
                max_occupants   = max_occ,
                min_stay_months = random.choice([1, 2, 3, 6]),
                title           = TITLES[i % len(TITLES)],
                city            = random.choice(CITIES),
                district        = random.choice(DISTRICTS),
                address         = f"{random.randint(1, 200)} El-{random.choice(['Nozha', 'Thawra', 'Mostafa', 'Hassan', 'Ahmed'])} Street",
                landmark        = random.choice(["Near metro station", "Near university", "Close to mall", "5 min from ring road", ""]),
                description     = random.choice(DESCRIPTIONS),
                ai_generated    = random.random() > 0.6,
                notes           = "",
                no_smoking      = no_smoking,
                pets_allowed    = pets_allowed,
                no_pets         = no_pets,
                males_only      = males_only,
                females_only    = females_only,
                wifi_included   = random.random() > 0.3,
                electricity_included = random.random() > 0.5,
                water_included  = random.random() > 0.5,
                fully_furnished = random.random() > 0.4,
                air_conditioning = random.random() > 0.5,
                study_desk      = random.random() > 0.5,
                quiet_after_10  = random.random() > 0.5,
                status          = 'active',
            )
            # attach one photo per listing
            img_url = ROOM_IMAGES[i % len(ROOM_IMAGES)]
            try:
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    img_data = resp.read()
                img_file = ContentFile(img_data, name=f'seed_{i}.jpg')
                ListingImage.objects.create(listing=listing, image=img_file, order=0)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Could not fetch image for listing {i}: {e}"))

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} listings."))
