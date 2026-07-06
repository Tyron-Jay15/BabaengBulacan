"""
Security helpers for BabaengBulacan.

Centralises:
- Field-level encryption (Fernet) for sensitive auth data (TOTP secrets)
- TOTP / 2FA helpers (secret generation, QR codes, verification)
- Backup recovery codes (generation, hashing, consumption)
- Request inspection (client IP, device/browser parsing)
- Authentication audit logging
- IP-based login rate limiting
- Device recognition (new-device detection)
"""
import base64
import hashlib
import io
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Field-level encryption (Fernet)
# ---------------------------------------------------------------------------
def _get_fernet():
    """Build a Fernet instance from FIELD_ENCRYPTION_KEY or derive from SECRET_KEY."""
    from cryptography.fernet import Fernet

    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or ''
    if key:
        key_bytes = key.encode() if isinstance(key, str) else key
    else:
        # Derive a stable 32-byte key from SECRET_KEY (dev fallback only).
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key_bytes = base64.urlsafe_b64encode(digest)
    return Fernet(key_bytes)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string, returning a base64 token string."""
    if plaintext is None:
        return ''
    token = _get_fernet().encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_value(token: str):
    """Decrypt a previously encrypted token string. Returns None on failure."""
    if not token:
        return None
    try:
        return _get_fernet().decrypt(token.encode('utf-8')).decode('utf-8')
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to decrypt value: %s", exc)
        return None


# ---------------------------------------------------------------------------
# TOTP / 2FA
# ---------------------------------------------------------------------------
def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret."""
    import pyotp
    return pyotp.random_base32()


def get_totp_provisioning_uri(secret: str, account_name: str) -> str:
    """Build an otpauth:// URI for enrolling in an authenticator app."""
    import pyotp
    issuer = getattr(settings, 'SITE_NAME', 'BabaengBulacan')
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code (allows 1 step of clock drift)."""
    import pyotp
    if not secret or not code:
        return False
    code = code.strip().replace(' ', '')
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception as exc:  # noqa: BLE001
        logger.error("TOTP verification error: %s", exc)
        return False


def generate_qr_code_data_uri(data: str) -> str:
    """Render a QR code for the given data and return it as a PNG data URI."""
    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#7B2CBF", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f"data:image/png;base64,{encoded}"


# ---------------------------------------------------------------------------
# Backup recovery codes
# ---------------------------------------------------------------------------
def generate_backup_codes(count=None):
    """Generate a list of human-friendly backup codes (plaintext, shown once)."""
    count = count or getattr(settings, 'BACKUP_CODE_COUNT', 10)
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(5).upper()  # 10 hex chars
        codes.append(f"{raw[:5]}-{raw[5:]}")
    return codes


def create_backup_codes_for_user(user):
    """Replace any existing backup codes with a fresh set. Returns plaintext codes."""
    from .models import BackupCode

    BackupCode.objects.filter(user=user).delete()
    codes = generate_backup_codes()
    BackupCode.objects.bulk_create([
        BackupCode(user=user, code_hash=make_password(code)) for code in codes
    ])
    return codes


def consume_backup_code(user, code: str) -> bool:
    """Validate and consume a backup code. Returns True if a code matched."""
    from .models import BackupCode

    if not code:
        return False
    code = code.strip().upper()
    for backup in BackupCode.objects.filter(user=user, used=False):
        if check_password(code, backup.code_hash):
            backup.used = True
            backup.used_at = timezone.now()
            backup.save(update_fields=['used', 'used_at'])
            return True
    return False


def count_unused_backup_codes(user) -> int:
    from .models import BackupCode
    return BackupCode.objects.filter(user=user, used=False).count()


# ---------------------------------------------------------------------------
# Request inspection
# ---------------------------------------------------------------------------
def get_client_ip(request):
    """Best-effort client IP extraction (respects X-Forwarded-For)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_device_info(request):
    """Parse the User-Agent into device/browser/os components."""
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    info = {
        'user_agent': ua_string,
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Unknown',
    }
    try:
        from user_agents import parse as ua_parse
        ua = ua_parse(ua_string)
        info['browser'] = (f"{ua.browser.family} {ua.browser.version_string}").strip()
        info['os'] = (f"{ua.os.family} {ua.os.version_string}").strip()
        if ua.is_mobile:
            info['device'] = 'Mobile'
        elif ua.is_tablet:
            info['device'] = 'Tablet'
        elif ua.is_pc:
            info['device'] = 'Desktop'
        elif ua.is_bot:
            info['device'] = 'Bot'
        if ua.device.family and ua.device.family != 'Other':
            info['device'] = f"{info['device']} ({ua.device.family})"
    except Exception as exc:  # noqa: BLE001
        logger.debug("UA parse failed: %s", exc)
    return info


def device_label(info) -> str:
    return f"{info.get('browser', 'Unknown')} on {info.get('os', 'Unknown')}"


# ---------------------------------------------------------------------------
# Authentication audit logging
# ---------------------------------------------------------------------------
def log_auth_event(request, event_type, user=None, success=True,
                   auth_method='', username_attempted='', details=''):
    """Write an AuthenticationLog entry. Never raises."""
    from .models import AuthenticationLog
    try:
        info = get_device_info(request)
        AuthenticationLog.objects.create(
            user=user,
            username_attempted=username_attempted or (user.username if user else ''),
            event_type=event_type,
            auth_method=auth_method,
            success=success,
            ip_address=get_client_ip(request),
            user_agent=info['user_agent'][:1000],
            device=info['device'][:120],
            browser=info['browser'][:120],
            os=info['os'][:120],
            details=details[:255],
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to write auth log (%s): %s", event_type, exc)


def record_failed_login(request, username_attempted='', user=None, reason=''):
    """Persist a FailedLoginAttempt row."""
    from .models import FailedLoginAttempt
    try:
        info = get_device_info(request)
        FailedLoginAttempt.objects.create(
            user=user,
            username_attempted=username_attempted,
            ip_address=get_client_ip(request),
            user_agent=info['user_agent'][:1000],
            reason=reason[:120],
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to record failed login: %s", exc)


# ---------------------------------------------------------------------------
# IP-based rate limiting (sliding-ish window via cache counter)
# ---------------------------------------------------------------------------
def _rate_key(request):
    return f"login_rate:{get_client_ip(request)}"


def is_rate_limited(request) -> bool:
    """Return True if this IP has exceeded the allowed login attempts."""
    max_attempts = getattr(settings, 'LOGIN_RATE_LIMIT_MAX', 10)
    count = cache.get(_rate_key(request), 0)
    return count >= max_attempts


def register_login_attempt(request):
    """Increment the rate-limit counter for this IP."""
    window = getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW', 300)
    key = _rate_key(request)
    try:
        count = cache.get(key, 0) + 1
        cache.set(key, count, timeout=window)
        return count
    except Exception:  # noqa: BLE001
        return 0


def reset_rate_limit(request):
    cache.delete(_rate_key(request))


def rate_limit_seconds_remaining(request) -> int:
    """Approximate seconds remaining in the rate-limit window."""
    # LocMemCache has no TTL introspection; return the configured window as a hint.
    return getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW', 300)


# ---------------------------------------------------------------------------
# Device recognition (new-device alerts)
# ---------------------------------------------------------------------------
DEVICE_COOKIE_NAME = 'bb_device_id'
DEVICE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def get_device_token(request):
    """Read the device token from the request cookie (or None)."""
    return request.COOKIES.get(DEVICE_COOKIE_NAME)


def is_known_device(user, device_token) -> bool:
    from .models import KnownDevice
    if not device_token:
        return False
    return KnownDevice.objects.filter(user=user, device_token=device_token).exists()


def remember_device(user, device_token, request):
    """Create or refresh a KnownDevice record. Returns (device, created)."""
    from .models import KnownDevice
    info = get_device_info(request)
    device, created = KnownDevice.objects.update_or_create(
        user=user,
        device_token=device_token,
        defaults={
            'label': device_label(info),
            'browser': info['browser'][:120],
            'os': info['os'][:120],
            'ip_address': get_client_ip(request),
            'last_seen': timezone.now(),
        },
    )
    return device, created


def new_device_token() -> str:
    return secrets.token_urlsafe(32)


def set_device_cookie(response, token):
    """Attach the device-recognition cookie to a response."""
    response.set_cookie(
        DEVICE_COOKIE_NAME,
        token,
        max_age=DEVICE_COOKIE_MAX_AGE,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    return response
