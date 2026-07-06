"""Production settings for PythonAnywhere and similar hosts."""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

_secret = os.getenv('SECRET_KEY', '').strip()
if not _secret or _secret.startswith('django-insecure-'):
    raise ImproperlyConfigured(
        'Set a strong SECRET_KEY in your environment (.env on PythonAnywhere). '
        'Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )
SECRET_KEY = _secret

_allowed = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
if not _allowed:
    raise ImproperlyConfigured(
        'Set ALLOWED_HOSTS in your environment, e.g. '
        'ALLOWED_HOSTS=yourusername.pythonanywhere.com'
    )
ALLOWED_HOSTS = _allowed

_csrf_origins = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if not _csrf_origins:
    _csrf_origins = [
        f'https://{host}' for host in _allowed
        if host and not host.startswith('.') and host != '*'
    ]
CSRF_TRUSTED_ORIGINS = _csrf_origins

STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405

# HTTPS / cookie security (PythonAnywhere terminates SSL at the edge)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# API: JSON only in production (no browsable API HTML)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
]

LOG_DIR = BASE_DIR / 'logs'  # noqa: F405
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
