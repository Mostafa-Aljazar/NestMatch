from django.shortcuts import render, redirect

from .models import SiteContent
from listings_app.models import Listing
from accounts_app.models import Testimonial
from django.contrib import messages
from .models import ContactMessage
import re


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

# faq view
def faq(request):
    return render(request, 'core_app/faq.html')

# contact view
def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        errors = {}

        # Name
        if len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters!'
        elif len(name) > 100:
            errors['name'] = 'Name must be under 100 characters!'

        # Email
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Please enter a valid email address!'

        # Message
        if len(message) < 10:
            errors['message'] = 'Message must be at least 10 characters!'
        elif len(message) > 2000:
            errors['message'] = 'Message must be under 2000 characters!'

        if not errors:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, "Your message has been sent! We'll get back to you within 24 hours.")
            return redirect('core_app:contact')
        else:
            messages.error(request, 'Please fix the errors below.')
            return render(request, 'core_app/contact.html', {'errors': errors, 'form_data': {'name': name, 'email': email, 'message': message}})

    return render(request, 'core_app/contact.html')



def privacy_policy(request):
    sections = [
        {
            'id': 'introduction',
            'title': 'Introduction',
            'content': '''
                <p>NestMatch ("we", "us", or "our") operates an AI-powered platform that helps people find compatible roommates. This Privacy Policy describes how we handle your personal information when you use our website, mobile experience, and related services.</p>
                <p>By creating an account or using NestMatch, you agree to the collection and use of information in accordance with this policy. We are committed to protecting your data and being transparent about how it powers your matches.</p>
            '''
        },
        {
            'id': 'information-we-collect',
            'title': 'Information We Collect',
            'content': '''
                <p>To match you effectively, we collect the following categories of information:</p>
                <ul class="space-y-3">
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Name.</strong> Your full name, used to personalize your profile and introductions.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Email address.</strong> Used for account access, verification, and important notifications.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Lifestyle preferences.</strong> Sleep schedule, cleanliness, social habits, pets, and other compatibility signals.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Location.</strong> Your city and preferred neighborhoods so we can match you with nearby roommates.</span></li>
                </ul>
            '''
        },
        {
            'id': 'how-we-use',
            'title': 'How We Use Your Information',
            'content': '''
                <p>We use the information we collect to:</p>
                <ul class="space-y-3">
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span>Generate compatibility scores and surface your best-fit roommate matches.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span>Create, maintain, and secure your NestMatch account.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span>Send relevant updates, match notifications, and service announcements.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span>Improve our matching algorithms and overall platform experience.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span>Detect, prevent, and respond to fraud, abuse, or security incidents.</span></li>
                </ul>
            '''
        },
        {
            'id': 'ai-compatibility',
            'title': 'AI & Compatibility Data',
            'content': '''
                <p>NestMatch uses <strong class="font-semibold text-gray-900">Google Gemini</strong> to analyze your lifestyle preferences and produce compatibility insights. Your responses are processed by Gemini to identify patterns and predict how well you'd live with potential roommates.</p>
                <p>This AI processing is limited to the lifestyle data you choose to share. We do not send your password or payment details to AI providers, and we never sell your data to third parties for advertising.</p>
            '''
        },
        {
            'id': 'third-party',
            'title': 'Third-Party Services',
            'content': '''
                <p>We rely on trusted third-party services to deliver core features:</p>
                <ul class="space-y-3">
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Google Maps.</strong> Powers location search, neighborhood data, and distance-based matching.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">WhatsApp.</strong> Enables matched users to connect and chat once both parties opt in.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Google Gemini AI.</strong> Processes lifestyle data to generate compatibility scores.</span></li>
                </ul>
                <p>Each provider has its own privacy practices. We encourage you to review their policies to understand how they handle data.</p>
            '''
        },
        {
            'id': 'data-security',
            'title': 'Data Security',
            'content': '''
                <p>We apply industry-standard safeguards to protect your information:</p>
                <ul class="space-y-3">
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">bcrypt.</strong> All passwords are hashed with bcrypt — we never store them in plain text.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">HTTPS.</strong> Data in transit is encrypted end-to-end using TLS over HTTPS.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">JWT.</strong> Sessions are authenticated with signed JSON Web Tokens to protect your account.</span></li>
                </ul>
                <p>While no system is ever completely impenetrable, we continuously review our practices to keep your data safe.</p>
            '''
        },
        {
            'id': 'your-rights',
            'title': 'Your Rights',
            'content': '''
                <p>You remain in control of your personal data. At any time you can:</p>
                <ul class="space-y-3">
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Access.</strong> Request a copy of the personal information we hold about you.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Edit.</strong> Update or correct your profile, preferences, and account details.</span></li>
                    <li class="flex gap-3"><span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500"></span><span><strong class="font-semibold text-gray-900">Delete.</strong> Permanently delete your account and associated data from NestMatch.</span></li>
                </ul>
                <p>To exercise any of these rights, visit your account settings or contact our privacy team.</p>
            '''
        },
{
    'id': 'contact',
    'title': 'Contact Us',
    'content': '''
        <p>If you have questions, concerns, or requests regarding this Privacy Policy or your data, we'd love to hear from you. You can reach our privacy team through our <a href="/contact/" class="font-semibold text-violet-600 hover:text-violet-700 underline-offset-4 hover:underline">Contact Us</a> page.</p>
        <p>We aim to respond to all privacy inquiries within two business days.</p>
    '''
},
    ]
    
    context = {
        'sections': sections,
    }
    
    return render(request, 'core_app/privacy_policy.html', context)
