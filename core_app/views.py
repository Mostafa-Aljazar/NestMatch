from django.shortcuts import render
from listings_app.models import Listing
from accounts_app.models import Testimonial


def index(request):
    latest_listings = Listing.objects.filter(status='active').select_related('poster').prefetch_related('images')[:3]
#    add filter(approved=True)
    reviews = Testimonial.objects.all().select_related('user')[:3]
    return render(request, 'core_app/landing.html', {
        'latest_listings': latest_listings,
        'reviews': reviews,
    })

def faq(request):
    return render(request, 'core_app/faq.html')
