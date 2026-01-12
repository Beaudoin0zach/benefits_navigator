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


def user_usage(request):
    """
    Add user's usage information to template context for freemium display.

    Available in templates as:
    - {{ user_usage.is_premium }}
    - {{ user_usage.documents_used }} / {{ user_usage.documents_limit }}
    - {{ user_usage.documents_remaining }}
    - {{ user_usage.storage_used_mb }} / {{ user_usage.storage_limit_mb }}
    - {{ user_usage.storage_percentage }}
    - {{ user_usage.denial_decodes_remaining }}
    - {{ user_usage.ai_analyses_remaining }}
    """
    if not request.user.is_authenticated:
        return {'user_usage': None}

    from accounts.models import UsageTracking

    try:
        usage, _ = UsageTracking.objects.get_or_create(user=request.user)
        return {'user_usage': usage.get_usage_summary()}
    except Exception:
        return {'user_usage': None}


def tier_limits(request):
    """
    Add tier limit settings to template context for display.

    Available as:
    - {{ tier_limits.free_documents }}
    - {{ tier_limits.free_storage_mb }}
    - {{ tier_limits.free_denial_decodes }}
    - {{ tier_limits.free_ai_analyses }}
    """
    return {
        'tier_limits': {
            'free_documents': getattr(settings, 'FREE_TIER_DOCUMENTS_PER_MONTH', 3),
            'free_storage_mb': getattr(settings, 'FREE_TIER_MAX_STORAGE_MB', 100),
            'free_denial_decodes': getattr(settings, 'FREE_TIER_DENIAL_DECODES_PER_MONTH', 2),
            'free_ai_analyses': getattr(settings, 'FREE_TIER_AI_ANALYSES_PER_MONTH', 5),
        }
    }


def feature_flags(request):
    """
    Add feature flags to template context.

    Available as:
    - {% if features.organizations %}...{% endif %}
    - {% if features.org_billing %}...{% endif %}

    Usage in templates:
        {% if features.organizations %}
            <a href="{% url 'accounts:org_dashboard' %}">My Organization</a>
        {% endif %}
    """
    from core.features import get_enabled_features

    return {
        'features': get_enabled_features(),
    }
