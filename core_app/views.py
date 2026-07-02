from django.shortcuts import render

from .models import SiteContent
from listings_app.models import Listing
from accounts_app.models import Testimonial


def index(request):
    content = SiteContent.load()

    latest_listings = (
        Listing.objects
        .filter(status='active')
        .select_related('poster')
        .prefetch_related('images')
        .order_by('-created_at')[:6]
    )

    reviews = (
        Testimonial.objects
        .filter(approved=True)
        .order_by('-created_at')[:6]
    )

    context = {
        'content':         content,
        'latest_listings': latest_listings,
        'reviews':         reviews,
    }
    return render(request, 'core_app/landing.html', context)