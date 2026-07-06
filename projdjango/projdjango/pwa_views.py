"""Progressive Web App — manifest, service worker, and install support."""
import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from projdjango.mobile_access import get_mobile_access_url, get_public_base_url

PWA_ICON_SIZES = (72, 96, 128, 144, 152, 192, 384, 512)


def _build_manifest(request):
    """Build manifest dict using environment-aware base URL."""
    base = get_public_base_url(request)
    start_url = get_mobile_access_url(request)
    static_base = base

    icons = [
        {
            'src': f'{static_base}/static/icons/icon-{size}.png',
            'sizes': f'{size}x{size}',
            'type': 'image/png',
            'purpose': 'any',
        }
        for size in PWA_ICON_SIZES
    ]
    icons.append({
        'src': f'{static_base}/static/icons/icon-512.png',
        'sizes': '512x512',
        'type': 'image/png',
        'purpose': 'maskable',
    })

    return {
        'id': '/',
        'name': getattr(settings, 'SITE_NAME', 'BabaengBulacan'),
        'short_name': 'BabaengBulacan',
        'description': (
            'Women Empowerment and Incident Reporting Platform — Province of Bulacan'
        ),
        'start_url': start_url,
        'scope': f'{base}/',
        'display': 'standalone',
        'display_override': ['standalone', 'browser'],
        'orientation': 'any',
        'background_color': '#ffffff',
        'theme_color': '#7B2CBF',
        'lang': 'en',
        'dir': 'ltr',
        'categories': ['social', 'utilities', 'government'],
        'prefer_related_applications': False,
        'icons': icons,
    }


@require_GET
@cache_control(max_age=300 if settings.DEBUG else 3600, public=True)
def web_manifest(request):
    """Serve dynamic web app manifest (also available as manifest.json)."""
    manifest = _build_manifest(request)
    return HttpResponse(
        json.dumps(manifest, indent=2),
        content_type='application/manifest+json',
    )


@require_GET
@cache_control(max_age=0, must_revalidate=True)
def service_worker(request):
    """Serve service worker with no long-term cache so updates apply quickly."""
    from django.contrib.staticfiles import finders

    path = finders.find('sw.js')
    body = "// Service worker not found\n"
    if path:
        with open(path, encoding='utf-8') as fh:
            body = fh.read()
    return HttpResponse(body, content_type='application/javascript')
