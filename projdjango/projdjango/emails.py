"""
Transactional email helpers for BabaengBulacan.

Each function renders a responsive, branded HTML template (with a plaintext
fallback) and sends it via Django's configured email backend. All functions are
defensive: a mail failure is logged but never breaks the request flow.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .security import get_device_info, get_client_ip

logger = logging.getLogger(__name__)


def _base_url():
    return getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')


def _site_ctx():
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'BabaengBulacan'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', 'Women Empowerment Platform'),
        'base_url': _base_url(),
        'year': timezone.now().year,
        'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
    }


def _send(subject, template, context, recipient):
    """Render `template` (+ .txt fallback if present) and send to `recipient`."""
    ctx = _site_ctx()
    ctx.update(context or {})
    try:
        html_body = render_to_string(f'emails/{template}.html', ctx)
        try:
            text_body = render_to_string(f'emails/{template}.txt', ctx)
        except Exception:  # noqa: BLE001
            text_body = strip_tags(html_body)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[recipient] if isinstance(recipient, str) else list(recipient),
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info("Sent '%s' email to %s (from %s)", template, recipient,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', ''))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send '%s' email to %s: %s", template, recipient, exc)
        return False


def _request_meta(request):
    """Capture IP/device details from a request for security-notice emails."""
    if request is None:
        return {'ip_address': 'Unknown', 'device': 'Unknown', 'browser': 'Unknown',
                'os': 'Unknown', 'when': timezone.now()}
    info = get_device_info(request)
    return {
        'ip_address': get_client_ip(request) or 'Unknown',
        'device': info['device'],
        'browser': info['browser'],
        'os': info['os'],
        'when': timezone.now(),
    }


# ---------------------------------------------------------------------------
# Public send functions
# ---------------------------------------------------------------------------
def send_verification_email(user, token, request=None):
    """Registration + email-verification message containing a time-limited link."""
    if request is not None:
        try:
            base = request.build_absolute_uri('/').rstrip('/')
        except Exception:  # noqa: BLE001
            base = _base_url()
    else:
        base = _base_url()
    link = f"{base.rstrip('/')}/accounts/verify-email/{token}/"
    hours = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_TTL', 86400) // 3600
    sent = _send(
        subject='Verify your BabaengBulacan account',
        template='verification',
        context={
            'user': user,
            'verify_link': link,
            'expires_hours': hours,
        },
        recipient=user.email,
    )
    return sent, link


def send_email_verified_notification(user):
    return _send(
        subject='Your email has been verified',
        template='email_verified',
        context={'user': user, 'login_link': f"{_base_url()}/accounts/login/"},
        recipient=user.email,
    )


def send_password_reset_email(user, token, request=None):
    link = f"{_base_url()}/accounts/reset-password/{token}/"
    minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_TTL', 3600) // 60
    ctx = {'user': user, 'reset_link': link, 'expires_minutes': minutes}
    ctx.update(_request_meta(request))
    return _send(
        subject='Reset your BabaengBulacan password',
        template='password_reset',
        context=ctx,
        recipient=user.email,
    )


def send_password_changed_notification(user, request=None):
    ctx = {'user': user}
    ctx.update(_request_meta(request))
    return _send(
        subject='Your password was changed',
        template='password_changed',
        context=ctx,
        recipient=user.email,
    )


def send_new_device_notification(user, request=None):
    ctx = {'user': user, 'profile_link': f"{_base_url()}/accounts/profile/"}
    ctx.update(_request_meta(request))
    return _send(
        subject='New sign-in to your BabaengBulacan account',
        template='new_device',
        context=ctx,
        recipient=user.email,
    )


def send_account_locked_notification(user, request=None, minutes=15):
    ctx = {'user': user, 'lockout_minutes': minutes}
    ctx.update(_request_meta(request))
    return _send(
        subject='Security alert: your account was temporarily locked',
        template='account_locked',
        context=ctx,
        recipient=user.email,
    )


def send_account_recovered_notification(user, request=None):
    ctx = {'user': user, 'login_link': f"{_base_url()}/accounts/login/"}
    ctx.update(_request_meta(request))
    return _send(
        subject='Your account was successfully recovered',
        template='account_recovered',
        context=ctx,
        recipient=user.email,
    )


def send_incident_status_email(incident, old_status, new_status):
    """Notify reporter when incident status changes."""
    status_labels = dict(incident.STATUS_CHOICES)
    ctx = {
        'incident': incident,
        'old_status': status_labels.get(old_status, old_status),
        'new_status': status_labels.get(new_status, new_status),
        'track_link': f"{_base_url()}/track-case/?id={incident.report_id}",
    }
    return _send(
        subject=f'Update on your incident report — {ctx["new_status"]}',
        template='incident_status',
        context=ctx,
        recipient=incident.email,
    )


def send_incident_assigned_email(incident, officer):
    """Notify reporter when an officer is assigned."""
    ctx = {
        'incident': incident,
        'officer_name': officer.get_full_name() or officer.username if officer else 'Staff',
        'track_link': f"{_base_url()}/track-case/?id={incident.report_id}",
    }
    return _send(
        subject='An officer has been assigned to your case',
        template='incident_assigned',
        context=ctx,
        recipient=incident.email,
    )
