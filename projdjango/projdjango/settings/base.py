"""
Shared Django settings for BabaengBulacan.
Environment-specific overrides live in development.py and production.py.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from project root and parent folder (ProjDjango/.env when manage.py lives in projdjango/)
for _env_path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    if _env_path.is_file():
        load_dotenv(_env_path, override=True)

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-p*4!v=dq+=pcp+fld$*bci+)kn8&n004lbs)c5-d8t$h%8!t^b',
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'projdjango.apps.ProjdjangoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'projdjango.middleware.SessionTimeoutMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'projdjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'projdjango.context_processors.security_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'projdjango.wsgi.application'

_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
_db_options = {}
if _db_engine.endswith('mysql'):
    _db_options = {
        'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }

DATABASES = {
    'default': {
        'ENGINE': _db_engine,
        'NAME': os.getenv('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': _db_options,
    }
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MAX_UPLOAD_SIZE = 52428800  # 50 MB

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Manila')
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security / auth policy
BUSINESS_HOURS_START = 6
BUSINESS_HOURS_END = 22
ALLOW_EMERGENCY_ACCESS = True
SESSION_TIMEOUT = 3600
SESSION_WARNING_TIME = 300
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = False

RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '6LcMuPYsAAAAAAp3KHHprgYWobDviQLeRvMiRmiR')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '6LcMuPYsAAAAABWo8QITV-kisdTfX8R1RmzXOocW')
RECAPTCHA_API_URL = 'https://www.google.com/recaptcha/api/siteverify'
RECAPTCHA_REQUIRED = os.getenv('RECAPTCHA_REQUIRED', 'True') == 'True'
# When False (default), skip CAPTCHA on LAN/localhost in DEBUG so mobile Wi-Fi testing works
RECAPTCHA_ENFORCE_ON_LAN = os.getenv('RECAPTCHA_ENFORCE_ON_LAN', 'False') == 'True'
# When False (default), allow password-only login on LAN in DEBUG (camera needs HTTPS on phones)
FACE_ENFORCE_ON_LAN = os.getenv('FACE_ENFORCE_ON_LAN', 'False') == 'True'

def _smtp_placeholder(value):
    """True when .env still has example/placeholder SMTP credentials."""
    if not value:
        return True
    lowered = value.strip().lower()
    return lowered in {
        'your-email@gmail.com',
        'your-app-password',
        'changeme',
        'change-me',
    } or lowered.startswith('your-')


EMAIL_HOST = os.getenv('EMAIL_HOST', '').strip()
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
SMTP_CONFIGURED = bool(
    EMAIL_HOST
    and EMAIL_HOST_USER
    and EMAIL_HOST_PASSWORD
    and not _smtp_placeholder(EMAIL_HOST_USER)
    and not _smtp_placeholder(EMAIL_HOST_PASSWORD)
)
if SMTP_CONFIGURED:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    if EMAIL_HOST and not SMTP_CONFIGURED:
        import logging
        logging.getLogger(__name__).warning(
            'EMAIL_HOST is set but SMTP credentials are missing or still placeholders. '
            'Using console email backend — verification links print in the runserver terminal.'
        )

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'BabaengBulacan <no-reply@babaengbulacan.local>')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
SITE_NAME = 'BabaengBulacan'
SITE_TAGLINE = 'Women Empowerment Platform'
LOGIN_URL = '/accounts/login/'
ADMIN_LOGIN_URL = '/accounts/admin/login/'

# PWA manifest — mobile entry URL (defaults to SITE_BASE_URL + /accounts/login/)
MOBILE_ACCESS_URL = os.getenv('MOBILE_ACCESS_URL', '').strip() or f'{SITE_BASE_URL}/accounts/login/'

FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', '').strip()
EMAIL_VERIFICATION_TOKEN_TTL = 60 * 60 * 24
# admin = safer: staff approves accounts in Admin Dashboard; email = user clicks inbox link
EMAIL_VERIFICATION_MODE = os.getenv('EMAIL_VERIFICATION_MODE', 'admin').strip().lower()
ADMIN_EMAIL_VERIFICATION = EMAIL_VERIFICATION_MODE == 'admin'
PASSWORD_RESET_TOKEN_TTL = 60 * 60
BACKUP_CODE_COUNT = 10
LOGIN_RATE_LIMIT_MAX = 10
LOGIN_RATE_LIMIT_WINDOW = 300
SEARCH_PAGE_SIZE = 5

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
