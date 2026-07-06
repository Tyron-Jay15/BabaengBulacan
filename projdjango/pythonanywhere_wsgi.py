"""
WSGI entry point for PythonAnywhere.

In the PythonAnywhere Web tab, set your WSGI configuration file to import
this module, or paste the contents of pythonanywhere_wsgi.py into the
default wsgi file and adjust paths.
"""
import os
import sys

# Ensure the project root is on the Python path
# Adjust if your clone path differs on PythonAnywhere
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_ENV', 'production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projdjango.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
