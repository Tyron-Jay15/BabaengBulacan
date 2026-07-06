"""Local development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '[::1]']

# Allow phones on the same Wi-Fi to connect via LAN IP (auto-detected for QR codes)
try:
    from projdjango.network_utils import get_local_ipv4

    _lan_ip = get_local_ipv4()
    if _lan_ip and _lan_ip not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_lan_ip)
except Exception:
    pass

INTERNAL_IPS = ['127.0.0.1', 'localhost']
