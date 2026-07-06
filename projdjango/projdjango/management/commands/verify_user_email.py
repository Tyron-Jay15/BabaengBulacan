"""Manually verify a user's email when SMTP is unavailable."""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from projdjango.models import UserProfile


class Command(BaseCommand):
    help = 'Mark a user email as verified so they can sign in (use when email delivery fails).'

    def add_arguments(self, parser):
        parser.add_argument('email', help='User email address to verify')

    def handle(self, *args, **options):
        email = options['email'].strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError(f'No user found with email: {email}') from exc

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.email_verified:
            self.stdout.write(self.style.WARNING(f'{email} is already verified.'))
            return

        profile.mark_email_verified()
        self.stdout.write(self.style.SUCCESS(f'Verified {email}. User can now sign in.'))
