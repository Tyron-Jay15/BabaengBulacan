"""Seed Bulacan municipalities, barangays, and a sample announcement for API demos."""
from django.db import migrations


def seed_locations(apps, schema_editor):
    Municipality = apps.get_model('projdjango', 'Municipality')
    Barangay = apps.get_model('projdjango', 'Barangay')
    Announcement = apps.get_model('projdjango', 'Announcement')

    data = {
        'Bulakan': ['San Jose', 'Bagumbayan', 'Bambang'],
        'Malolos': ['San Gabriel', 'Anilao', 'Atlag'],
        'Meycauayan': ['Poblacion', 'Calvario', 'Bahay Pare'],
    }
    for muni_name, barangays in data.items():
        muni, _ = Municipality.objects.get_or_create(name=muni_name, defaults={'province': 'Bulacan'})
        for brgy in barangays:
            Barangay.objects.get_or_create(name=brgy, municipality=muni)

    Announcement.objects.get_or_create(
        title='Welcome to BabaengBulacan',
        defaults={
            'description': (
                'BabaengBulacan is Bulacan\'s Women Empowerment and Incident Reporting platform. '
                'Report incidents safely, track your case, and access community resources.'
            ),
            'is_published': True,
        },
    )


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projdjango', '0010_barangay_municipality_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_locations, unseed),
    ]
