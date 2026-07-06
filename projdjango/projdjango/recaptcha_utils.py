"""reCAPTCHA helpers — show on web; relax only for mobile QR / LAN testing."""
from django.conf import settings


def get_request_host(request):
    if request is None:
        return ''
    return request.get_host().split(':')[0].lower().strip('[]')


def is_localhost_host(host):
    return host in ('localhost', '127.0.0.1', '::1')


def is_lan_ip_host(host):
    """Private LAN IPs (e.g. 192.168.x.x) — typical mobile QR Wi-Fi access."""
    if not host or is_localhost_host(host):
        return False
    if host.startswith('192.168.'):
        return True
    if host.startswith('10.'):
        return True
    if host.startswith('172.'):
        parts = host.split('.')
        if len(parts) >= 2 and parts[1].isdigit():
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    return False


def is_lan_or_local_host(host):
    """Localhost or private LAN — used for QR URL detection etc."""
    return is_localhost_host(host) or is_lan_ip_host(host)


def is_mobile_user_agent(request):
    """Detect phone/tablet browsers (server-side)."""
    if request is None:
        return False
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_markers = (
        'android', 'iphone', 'ipad', 'ipod', 'mobile',
        'webos', 'blackberry', 'opera mini', 'silk/',
    )
    return any(marker in ua for marker in mobile_markers)


def is_mobile_lan_dev_access(request):
    """
    True when a phone/tablet opens the site via LAN IP in DEBUG mode.
    This is the only case where CAPTCHA/face are relaxed for QR testing.
    """
    if not settings.DEBUG or request is None:
        return False
    return is_lan_ip_host(get_request_host(request)) and is_mobile_user_agent(request)


def should_show_recaptcha(request):
    """
    Whether to render and enforce reCAPTCHA.

    - Desktop web (including localhost): always shown when configured.
    - Mobile on LAN IP in DEBUG (QR Wi-Fi test): hidden unless RECAPTCHA_ENFORCE_ON_LAN=True.
    - Production HTTPS: always shown.
    """
    if not getattr(settings, 'RECAPTCHA_SECRET_KEY', ''):
        return False
    if not getattr(settings, 'RECAPTCHA_REQUIRED', True):
        return False
    if is_mobile_lan_dev_access(request):
        return getattr(settings, 'RECAPTCHA_ENFORCE_ON_LAN', False)
    return True


def captcha_required_for_request(request):
    """Whether server-side CAPTCHA validation must pass for this request."""
    return should_show_recaptcha(request)
