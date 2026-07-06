"""
Template context processors for BabaengBulacan.
"""
from django.conf import settings


def security_context(request):
    """Inject security and mobile-access settings into every template."""
    from projdjango.mobile_access import get_mobile_context
    from projdjango.recaptcha_utils import (
        get_request_host,
        is_lan_or_local_host,
        is_mobile_lan_dev_access,
        should_show_recaptcha,
    )

    host = get_request_host(request)
    ctx = {
        'RECAPTCHA_SITE_KEY': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
        'RECAPTCHA_ENABLED': bool(getattr(settings, 'RECAPTCHA_SECRET_KEY', '')),
        'RECAPTCHA_SHOW': should_show_recaptcha(request),
        'IS_LAN_DEV_ACCESS': settings.DEBUG and is_lan_or_local_host(host),
        'IS_MOBILE_LAN_DEV': is_mobile_lan_dev_access(request),
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'BabaengBulacan'),
        'ADMIN_EMAIL_VERIFICATION': getattr(settings, 'ADMIN_EMAIL_VERIFICATION', True),
    }
    ctx.update(get_mobile_context(request))
    return ctx
