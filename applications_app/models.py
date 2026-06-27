from django.conf import settings
from django.db import models

from listings_app.models import Listing


class Application(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    seeker            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    listing           = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='applications')
    message           = models.TextField(blank=True)
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    compatibility     = models.PositiveSmallIntegerField(null=True, blank=True, help_text="AI compatibility score 0–100")
    applied_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
    poster_note       = models.TextField(blank=True, help_text="Optional note from poster on accept/reject")

    class Meta:
        unique_together = ['seeker', 'listing']
        ordering        = ['-applied_at']

    def __str__(self):
        return f"{self.seeker} → {self.listing} [{self.status}]"

    @property
    def compatibility_label(self):
        if self.compatibility is None:
            return None
        if self.compatibility >= 80:
            return 'Excellent'
        if self.compatibility >= 60:
            return 'Good'
        return 'Low'

    @property
    def compatibility_color(self):
        if self.compatibility is None:
            return 'gray'
        if self.compatibility >= 80:
            return 'violet'
        if self.compatibility >= 60:
            return 'amber'
        return 'rose'
