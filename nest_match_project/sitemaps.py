# Import the base Sitemap class from Django.
# This class is responsible for auto-generating the sitemap.xml file
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

# Import the Listing model from the listings_app app
# so we can pull all the rooms from the database
from listings_app.models import Listing


# Create a new class called ListingSitemap that inherits from Sitemap
# This class defines "how" Django builds the sitemap entries for room pages
class ListingSitemap(Sitemap):

    # changefreq: tells Google how often this content is expected to change
    # (e.g. price or availability might change) — this is just a "hint" for
    # Google, not a strict rule, but it helps it decide how often to re-crawl
    changefreq = "daily"

    # priority: a number from 0.0 to 1.0 indicating how important these pages
    # are compared to the rest of your site (the hidden default is 0.5)
    # 0.8 = "fairly important" since these are your core product pages (rooms)
    priority = 0.8

    # This method is the "heart" of the Sitemap class
    # It must return a QuerySet or list of every item (every room)
    # you want to appear in the sitemap
    def items(self):
        # Only fetch listings where status = 'active'
        # meaning they are published and actually visible to users
        # (we avoid is_active here because it's a @property, not a real
        # database field, so it can't be used inside filter())
        return Listing.objects.filter(status='active')

    # This method runs once for "each" item returned by items()
    # (obj here is a single Listing object each time it's called)
    # It must return the last-modified date for that page
    # Google uses this date to know if the page content is "fresh" or not
    def lastmod(self, obj):
        # updated_at is a real field on the model (auto_now=True),
        # so it updates automatically every time the listing is saved
        return obj.updated_at

    # This method defines the actual URL for each room,
    # which is what will appear inside the sitemap.xml file
    def location(self, obj):
        # Build the URL manually using the room's primary key (obj.pk)
        # NOTE: double-check this matches the actual room detail URL
        # pattern in listings_app/urls.py
        # (i.e. confirm it's really /rooms/<pk>/ and not something like
        # /rooms/detail/<pk>/)
        return reverse('listings_app:room_detail', args=[obj.pk])