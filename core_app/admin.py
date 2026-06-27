from django.contrib import admin
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'role', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'role', 'rating')
    search_fields = ('reviewer_name', 'quote', 'location')
    ordering = ('-created_at',)
