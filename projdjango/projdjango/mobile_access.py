"""
Mobile access helpers for BabaengBulacan (PWA manifest, LAN URLs in development).

Production uses SITE_BASE_URL / MOBILE_ACCESS_URL.
Development detects LAN IP so phones on the same Wi-Fi can open the site directly.
"""
import logging

from django.conf import settings

from projdjango.network_utils import check_lan_server_access, get_local_ipv4

logger = logging.getLogger(__name__)


def _parse_port_from_host(host):
    if not host:
        return 8000
    host = host.split(':')
    if len(host) == 2 and host[1].isdigit():
        return int(host[1])
    return 443 if settings.DEBUG is False else 8000


def get_dev_port(request=None):
    default = int(getattr(settings, 'DEV_SERVER_PORT', 8000))
    if request is None:
        return default

    host = request.META.get('HTTP_HOST', '')
    if host and ':' in host:
        return _parse_port_from_host(host)

    if not is_production_mode():
        return default

    try:
        return int(request.get_port())
    except (ValueError, AttributeError, TypeError):
        return default


def is_production_mode():
    return not getattr(settings, 'DEBUG', True)


def get_public_base_url(request=None):
    """
    Base URL for PWA manifest and mobile sharing.

    Production: SITE_BASE_URL (or MOBILE_ACCESS_URL without path).
    Development: http://<detected-lan-ipv4>:<port>
    """
    explicit = getattr(settings, 'MOBILE_ACCESS_URL', '').strip()
    if explicit and is_production_mode():
        base = explicit.rstrip('/')
        if '/accounts/' in base:
            base = base.split('/accounts/')[0]
        return base

    if is_production_mode():
        return getattr(settings, 'SITE_BASE_URL', '').rstrip('/')

    local_ip = get_local_ipv4()
    port = get_dev_port(request)
    if local_ip:
        return f'http://{local_ip}:{port}'

    logger.warning('Local IPv4 not detected; phones on Wi-Fi may need your computer IP manually.')
    return getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')


def get_mobile_access_url(request=None):
    """Default entry URL for PWA / mobile bookmarks."""
    return f'{get_public_base_url(request).rstrip("/")}/accounts/login/'


def get_mobile_context(request):
    """Template context for mobile/PWA hints."""
    url = get_mobile_access_url(request)
    port = get_dev_port(request)
    local_ip = get_local_ipv4()
    lan_ok = True
    network_warning = ''

    if not is_production_mode():
        lan_ok, network_warning = check_lan_server_access(local_ip, port)

    return {
        'MOBILE_ACCESS_URL': url,
        'SITE_BASE_URL': get_public_base_url(request),
        'MOBILE_LOCAL_IP': local_ip or '',
        'MOBILE_IS_PRODUCTION': is_production_mode(),
        'MOBILE_LAN_ACCESSIBLE': lan_ok,
        'MOBILE_NETWORK_WARNING': network_warning,
    }


def log_startup_network_info():
    """Log how to open the site from a phone when Django starts (development only)."""
    if is_production_mode():
        logger.info('Mobile/PWA production URL: %s', get_mobile_access_url())
        return
    local_ip = get_local_ipv4()
    port = getattr(settings, 'DEV_SERVER_PORT', 8000)
    if local_ip:
        url = f'http://{local_ip}:{port}/'
        lan_ok, warn = check_lan_server_access(local_ip, port)
        if lan_ok:
            logger.info('Open on your phone (same Wi-Fi): %s', url)
        else:
            logger.warning('%s Phone URL would be: %s', warn, url)
    else:
        logger.warning('Could not detect LAN IP for mobile access.')
