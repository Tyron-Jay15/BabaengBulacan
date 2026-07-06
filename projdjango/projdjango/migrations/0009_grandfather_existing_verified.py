"""
Data migration: mark all pre-existing user accounts as email-verified.

This grandfathers current users in so the new email-verification requirement
does not lock anyone out of their existing account. New registrations created
after this migration must still verify their email address.
"""
from django.db import migrations
from django.utils import timezone


def grandfather_existing_users(apps, schema_editor):
    UserProfile = apps.get_model('projdjango', 'UserProfile')
    now = timezone.now()
    UserProfile.objects.filter(email_verified=False).update(
        email_verified=True,
        email_verified_at=now,
    )


def reverse_noop(apps, schema_editor):
    # Intentionally irreversible-safe: we don't un-verify users on rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projdjango', '0008_userprofile_email_verified_and_more'),
    ]

    operations = [
        migrations.RunPython(grandfather_existing_users, reverse_noop),
    ]
