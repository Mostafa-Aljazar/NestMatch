from django.contrib import admin
from .models import Agreement


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'listing', 'poster', 'version', 'is_fallback', 'created_at')
    list_filter = ('is_fallback',)
    search_fields = ('tenant__email', 'poster__email', 'listing__title')
    readonly_fields = ('created_at', 'updated_at')
