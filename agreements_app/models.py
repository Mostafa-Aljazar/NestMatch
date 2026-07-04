from django.conf import settings
from django.db import models

from applications_app.models import Application


def agreement_pdf_upload_to(instance, filename):
    return f'agreements/{instance.application_id}/agreement_{instance.pk or "new"}.pdf'


class Agreement(models.Model):
    """
    One AI-generated rental agreement per accepted Application. Immutable
    once generated — unlike compatibility_app.CompatibilityScore, this is a
    document a user may have already downloaded and relied on, so later
    listing/profile edits never silently rewrite it. Regeneration is an
    explicit poster action (see agreements_app.service.regenerate_agreement)
    that bumps `version` and overwrites the text/PDF in place.
    """
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='agreement')
    listing = models.ForeignKey('listings_app.Listing', on_delete=models.CASCADE, related_name='agreements')
    poster  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agreements_as_poster')
    tenant  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agreements_as_tenant')

    generated_text = models.TextField(help_text="Full agreement body, Gemini-authored or template fallback")
    is_fallback    = models.BooleanField(default=False, help_text="True if Gemini was unavailable and a template fallback was used")
    pdf_file       = models.FileField(upload_to=agreement_pdf_upload_to, null=True, blank=True)
    version        = models.PositiveSmallIntegerField(default=1)

    poster_signed_name = models.CharField(max_length=150, blank=True)
    poster_signed_at   = models.DateTimeField(null=True, blank=True)
    tenant_signed_name = models.CharField(max_length=150, blank=True)
    tenant_signed_at   = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Agreement v{self.version} — {self.tenant} × {self.listing}'

    @property
    def is_fully_signed(self):
        return bool(self.poster_signed_at and self.tenant_signed_at)
