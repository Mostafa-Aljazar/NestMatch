"""
Custom SocialAccountAdapter for django-allauth.

WHY THIS FILE EXISTS:
By default, allauth shows an intermediate "choose a username" form
(the unstyled /auth/3rdparty/signup/ page) whenever it cannot guarantee
that auto-generated user data will pass our custom User model's
validation (our username field has a strict regex). This adapter takes
over username generation BEFORE allauth tries to render that form, so
it always succeeds automatically and the manual form never appears.
"""

import re
import uuid

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NestMatchSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.username:
            base = (data.get('email') or 'user').split('@')[0]
            user.username = self._generate_unique_username(base)

        return user

    @staticmethod
    def _generate_unique_username(base):
        # Import here (not top-level) to avoid circular imports between
        # accounts_app.models and accounts_app.adapters at app load time.
        from .models import User

        cleaned = re.sub(r'[^a-zA-Z0-9_.]', '', base).lower()
        if len(cleaned) < 3:
            cleaned = f'user{cleaned}'
        cleaned = cleaned[:24]

        candidate = cleaned
        while User.objects.filter(username__iexact=candidate).exists():
            suffix = uuid.uuid4().hex[:6]
            candidate = f'{cleaned}{suffix}'[:30]

        return candidate

    def pre_social_login(self, request, sociallogin):
        """
        Called right before a social login is processed, but after the
        provider (Google) has been contacted successfully.

        If someone already has an account with this exact email (registered
        normally with email/password), we link this Google login to that
        existing account instead of blocking it as an error -- this is the
        standard "account linking by verified email" pattern.
        """
        if sociallogin.is_existing:
            # Already linked to a social account before — nothing to do.
            return

        email = sociallogin.account.extra_data.get('email', '').strip().lower()
        if not email:
            return

        from .models import User

        try:
            existing_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # Connect this Google login to the existing account.
        sociallogin.connect(request, existing_user)