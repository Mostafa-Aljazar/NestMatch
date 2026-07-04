from accounts_app.models import Testimonial

from django.db import models


class SiteContent(models.Model):
    """
    Singleton model holding all editable landing-page content.
    There should only ever be one row (pk=1). Use SiteContent.load()
    to fetch-or-create it instead of querying directly.
    """

    # ── Hero section ──────────────────────────────────────────────────────────
    hero_badge_text  = models.CharField(max_length=60,  default='AI-Powered Matching')
    hero_title_line1 = models.CharField(max_length=80,  default='Find Your Perfect')
    hero_title_line2 = models.CharField(max_length=80,  default='Roommate & Room')
    hero_subtitle    = models.TextField(
        max_length=300,
        default='NestMatch uses AI to match you with compatible roommates based on '
                 'your lifestyle — sleep habits, cleanliness, noise level, and more.'
    )
    hero_cta_primary_text    = models.CharField(max_length=40, default='Get Started')
    hero_cta_primary_url     = models.CharField(max_length=200, default='/auth/')
    hero_cta_secondary_text  = models.CharField(max_length=40, default='Browse Rooms')
    hero_cta_secondary_url   = models.CharField(max_length=200, default='/rooms/')
    hero_feature_tag_1 = models.CharField(max_length=40, default='Free to use')
    hero_feature_tag_2 = models.CharField(max_length=40, default='AI Compatibility')
    hero_feature_tag_3 = models.CharField(max_length=40, default='Instant WhatsApp')

    # ── Stats bar ─────────────────────────────────────────────────────────────
    stat_1_value = models.CharField(max_length=20, default='2,400+')
    stat_1_label = models.CharField(max_length=40, default='Active Listings')
    stat_2_value = models.CharField(max_length=20, default='8,500+')
    stat_2_label = models.CharField(max_length=40, default='Happy Users')
    stat_3_value = models.CharField(max_length=20, default='12+')
    stat_3_label = models.CharField(max_length=40, default='Cities')
    stat_4_value = models.CharField(max_length=20, default='94%')
    stat_4_label = models.CharField(max_length=40, default='Match Accuracy')

    # ── How it Works section ─────────────────────────────────────────────────
    how_it_works_eyebrow     = models.CharField(max_length=40,  default='How it Works')
    how_it_works_title       = models.CharField(max_length=120, default='Find your match in 3 simple steps')
    how_it_works_subtitle    = models.CharField(max_length=200, default='From sign-up to move-in, NestMatch makes the process seamless')

    step_1_icon  = models.CharField(max_length=10,  default='📝')
    step_1_title = models.CharField(max_length=60,  default='Create Your Profile')
    step_1_text  = models.TextField(max_length=250, default='Sign up and fill out your lifestyle questionnaire — sleep time, cleanliness, noise level, smoking habits and more')

    step_2_icon  = models.CharField(max_length=10,  default='🔍')
    step_2_title = models.CharField(max_length=60,  default='Browse & Match')
    step_2_text  = models.TextField(max_length=250, default='Search rooms with live filters. See AI compatibility scores instantly for every listing you browse')

    step_3_icon  = models.CharField(max_length=10,  default='🤝')
    step_3_title = models.CharField(max_length=60,  default='Connect & Move In')
    step_3_text  = models.TextField(max_length=250, default='Apply to rooms, chat via WhatsApp, and generate your rental agreement with AI in seconds')

    # ── CTA (bottom) section ─────────────────────────────────────────────────
    cta_eyebrow  = models.CharField(max_length=40,  default='Get Started Today')
    cta_title    = models.CharField(max_length=120, default='Ready to Find Your Perfect Nest?')
    cta_subtitle = models.CharField(max_length=200, default='Join 8,500+ users already finding their perfect roommate match with AI')
    cta_primary_text   = models.CharField(max_length=40,  default='Post a Room')
    cta_primary_url    = models.CharField(max_length=200, default='/rooms/new/')
    cta_secondary_text = models.CharField(max_length=40,  default='Find a Room')
    cta_secondary_url  = models.CharField(max_length=200, default='/rooms/')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Content'
        verbose_name_plural = 'Site Content'

    def __str__(self):
        return 'Landing Page Content'

    def save(self, *args, **kwargs):
        # Enforce singleton: always save as pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.email}"

    class Meta:
        ordering = ['-created_at']
