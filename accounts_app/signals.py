"""
Signal handlers connecting django-allauth's social-login flow to our
custom User model.
"""

#import re
import uuid

import requests
from allauth.account.signals import user_signed_up
from django.core.files.base import ContentFile
from django.dispatch import receiver

from .models import User


# def _generate_unique_username(base):
#     cleaned = re.sub(r'[^a-zA-Z0-9_.]', '', base).lower()
#     if len(cleaned) < 3:
#         cleaned = f'user{cleaned}'
#     cleaned = cleaned[:24]

#     candidate = cleaned
#     while User.objects.filter(username__iexact=candidate).exists():
#         suffix = uuid.uuid4().hex[:6]
#         candidate = f'{cleaned}{suffix}'[:30]

#     return candidate


def _download_google_profile_picture(user, picture_url):
    """
    Downloads the image at picture_url and attaches it to user.profile_pic.
    Fails silently on any network/image error -- a broken avatar download
    should never block account creation.
    """
    if not picture_url:
        return

    try:
        response = requests.get(f'{picture_url}?sz=512', timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return

    content_type = response.headers.get('Content-Type', '')
    if 'image' not in content_type:
        return

    extension = 'jpg' if 'jpeg' in content_type else content_type.split('/')[-1]
    filename = f'google_avatar_{user.pk or uuid.uuid4().hex[:8]}.{extension}'

    user.profile_pic.save(filename, ContentFile(response.content), save=False)


@receiver(user_signed_up)
def populate_new_social_user(sender, request, user, **kwargs):
    sociallogin = kwargs.get('sociallogin')
    if sociallogin is None or sociallogin.account.provider != 'google':
        return

    extra_data = sociallogin.account.extra_data

    first_name = extra_data.get('given_name', '')
    last_name = extra_data.get('family_name', '')
    if not first_name and not last_name:
        full_name = extra_data.get('name', '')
        parts = full_name.split(' ', 1)
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''

    user.first_name = first_name or user.first_name or 'New'
    user.last_name = last_name or user.last_name or 'User'
    user.auth_provider = 'google'
    user.set_unusable_password()

    # if not user.username:
    #     base = extra_data.get('email', 'user').split('@')[0]
    #     user.username = _generate_unique_username(base)

    # Download once, on first sign-up only
    _download_google_profile_picture(user, extra_data.get('picture'))

    user.save()