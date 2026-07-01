from django.shortcuts import render, redirect
from listings_app.models import Listing
from accounts_app.models import Testimonial
from django.contrib import messages
from .models import ContactMessage


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

def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, "Your message has been sent! We'll get back to you within 24 hours.")
            return redirect('core_app:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')
    return render(request, 'core_app/contact.html')