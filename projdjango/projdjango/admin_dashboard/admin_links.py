"""Build grouped links into Django's built-in admin site."""
from django.contrib import admin
from django.urls import NoReverseMatch, reverse

# Friendly group labels for the backend hub page
APP_SECTIONS = [
    ('auth', 'Users & Groups'),
    ('projdjango', 'BabaengBulacan Data'),
]

APP_LABEL_OVERRIDES = {
    'auth': 'Users & Groups',
    'projdjango': 'BabaengBulacan Data',
}


def get_django_admin_sections(request):
    """
    Return registered Django admin models grouped by app for the backend hub.
    Each item: {name, url, add_url (optional)}
    """
    grouped = {}

    for model, model_admin in admin.site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        try:
            changelist_url = reverse(f'admin:{app_label}_{model_name}_changelist')
        except NoReverseMatch:
            continue

        add_url = None
        if model_admin.has_add_permission(request):
            try:
                add_url = reverse(f'admin:{app_label}_{model_name}_add')
            except NoReverseMatch:
                pass

        grouped.setdefault(app_label, []).append({
            'name': str(model._meta.verbose_name_plural).title(),
            'url': changelist_url,
            'add_url': add_url,
        })

    sections = []
    seen_apps = set()

    for app_label, label in APP_SECTIONS:
        models = grouped.get(app_label, [])
        if models:
            sections.append({
                'label': label,
                'models': sorted(models, key=lambda m: m['name']),
            })
            seen_apps.add(app_label)

    for app_label, models in sorted(grouped.items()):
        if app_label in seen_apps:
            continue
        sections.append({
            'label': APP_LABEL_OVERRIDES.get(app_label, app_label.title()),
            'models': sorted(models, key=lambda m: m['name']),
        })

    return sections
