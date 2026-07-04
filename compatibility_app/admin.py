from django.contrib import admin

from .models import CompatibilityScore


@admin.register(CompatibilityScore)
class CompatibilityScoreAdmin(admin.ModelAdmin):
    list_display = ('seeker', 'listing', 'overall_score', 'is_fallback', 'computed_at')
    list_filter = ('is_fallback',)
