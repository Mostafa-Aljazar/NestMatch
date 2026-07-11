from .models import PlatformSettings


def platform_settings(request):
    return {'platform_settings': PlatformSettings.load()}
