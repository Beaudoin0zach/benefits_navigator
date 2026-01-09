"""
Custom context processors for making variables available to all templates
"""

from django.conf import settings


def site_settings(request):
    """
    Add site-wide settings to template context
    """
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DESCRIPTION': settings.SITE_DESCRIPTION,
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'DEBUG': settings.DEBUG,
    }
