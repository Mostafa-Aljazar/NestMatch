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


class ListingReviewManager(models.Manager):

    def create_from_post(self, listing, reviewer, post_data):
        """
        Validate that the reviewer has an accepted application for this listing,
        then create and return a ListingReview. Raises ValidationError on failure.
        """
        from django.core.exceptions import ValidationError

        has_accepted = Application.objects.filter(
            listing=listing, seeker=reviewer, status=Application.STATUS_ACCEPTED
        ).exists()
        if not has_accepted:
            raise ValidationError({'permission': ['Only accepted applicants can review this listing.']})

        if self.filter(listing=listing, reviewer=reviewer).exists():
            raise ValidationError({'duplicate': ['You have already reviewed this listing.']})

        errors = {}

        try:
            rating = int(post_data.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            errors['rating'] = ['Please select a rating between 1 and 5.']

        comment = post_data.get('comment', '').strip()
        if not comment:
            errors['comment'] = ['A comment is required.']
        elif len(comment) > 2000:
            errors['comment'] = ['Comment cannot exceed 2000 characters.']

        if errors:
            raise ValidationError(errors)

        return self.create(listing=listing, reviewer=reviewer, rating=rating, comment=comment[:2000])


class ListingReview(models.Model):
    listing    = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listing_reviews')
    rating     = models.PositiveSmallIntegerField()
    comment    = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ListingReviewManager()

    class Meta:
        unique_together = ['listing', 'reviewer']
        ordering        = ['-created_at']

    def __str__(self):
        return f'{self.reviewer} rated {self.listing} {self.rating}/5'
