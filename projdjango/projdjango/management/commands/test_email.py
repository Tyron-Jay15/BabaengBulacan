"""Test SMTP configuration by sending a sample email."""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP settings in .env'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            nargs='?',
            default='',
            help='Email address to send the test to (defaults to EMAIL_HOST_USER)',
        )

    def handle(self, *args, **options):
        recipient = (options['recipient'] or getattr(settings, 'EMAIL_HOST_USER', '')).strip()
        if not recipient:
            self.stderr.write('Provide a recipient email or set EMAIL_HOST_USER in .env')
            return

        self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'SMTP configured: {getattr(settings, "SMTP_CONFIGURED", False)}')
        self.stdout.write(f'Sending test to: {recipient}')

        try:
            send_mail(
                subject='BabaengBulacan — test email',
                message='If you received this, SMTP is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'FAILED: {exc}'))
            self.stderr.write(
                '\nFor Gmail: use an App Password (not your login password).\n'
                'https://myaccount.google.com/apppasswords\n'
            )
            return

        if 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                'Console backend — email printed above, not delivered to inbox. '
                'Set EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD in .env for real delivery.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'Test email sent to {recipient}.'))
