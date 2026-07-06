"""
Load development or production settings based on DJANGO_ENV.

Local dev (default):
    DJANGO_ENV=development  →  projdjango.settings.development

PythonAnywhere / production:
    DJANGO_ENV=production   →  projdjango.settings.production
"""
import os

_env = os.getenv('DJANGO_ENV', 'development').lower()

if _env == 'production':
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
