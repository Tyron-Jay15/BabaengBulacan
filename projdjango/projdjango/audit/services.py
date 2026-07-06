"""System-wide audit logging service."""

from projdjango.models import AuditLog
from projdjango import security


def log_action(request, action, *, object_type='', object_id='', details='', user=None):
    """
    Record an audit log entry with request metadata.

    Usage:
        log_action(request, 'status_changed', object_type='IncidentReport',
                   object_id=report.report_id, details='submitted → under_review')
    """
    actor = user or (request.user if request and request.user.is_authenticated else None)
    ip = security.get_client_ip(request) if request else None
    info = security.get_device_info(request) if request else {'browser': ''}

    return AuditLog.objects.create(
        user=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id else '',
        ip_address=ip,
        browser=info.get('browser', ''),
        details=details,
    )
