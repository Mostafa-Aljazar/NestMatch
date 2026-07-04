from django.conf import settings
from django.db import models


class CompatibilityScore(models.Model):
    """
    Cached Gemini-computed compatibility score for one (seeker, listing) pair.
    Trusted only while profile_updated_at/listing_updated_at still match the
    live LifestyleProfile/Listing rows — see compatibility_app.scoring.
    """
    seeker  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compatibility_scores')
    listing = models.ForeignKey('listings_app.Listing', on_delete=models.CASCADE, related_name='compatibility_scores')

    overall_score        = models.PositiveSmallIntegerField()
    sleep_schedule_match = models.PositiveSmallIntegerField(default=0)
    cleanliness_match    = models.PositiveSmallIntegerField(default=0)
    noise_match          = models.PositiveSmallIntegerField(default=0)
    breakdown_summary    = models.TextField(blank=True)
    is_fallback          = models.BooleanField(default=False)

    profile_updated_at = models.DateTimeField()
    listing_updated_at = models.DateTimeField()
    computed_at         = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('seeker', 'listing')

    def __str__(self):
        return f'{self.seeker} × {self.listing}: {self.overall_score}%'
