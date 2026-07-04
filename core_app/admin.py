from django.contrib import admin
from .models import Testimonial
from .models import ContactMessage


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'role', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'role', 'rating')
    search_fields = ('reviewer_name', 'quote', 'location')
    ordering = ('-created_at',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'created_at']
    readonly_fields = ['name', 'email', 'message', 'created_at']
    ordering      = ['-created_at']

