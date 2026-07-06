"""Case management business logic — timeline, assignment, evidence, notifications."""

import os
from django.conf import settings
from django.utils import timezone

from projdjango.models import (
    CaseAssignment,
    CaseTimeline,
    Evidence,
    IncidentReport,
    Notification,
)


def _status_timeline_event(status):
    mapping = {
        'submitted': 'submitted',
        'under_review': 'under_review',
        'resolved': 'resolved',
        'closed': 'closed',
    }
    return mapping.get(status, 'status_updated')


def add_timeline_event(incident, event_type, title, *, actor=None, description='', metadata=None):
    return CaseTimeline.objects.create(
        incident=incident,
        event_type=event_type,
        title=title,
        description=description,
        actor=actor,
        metadata=metadata or {},
    )


def record_status_change(incident, old_status, new_status, actor, request=None):
    """Update status, write timeline + notification + audit (audit called by caller)."""
    if old_status == new_status:
        return incident

    incident.status = new_status
    incident.save(update_fields=['status', 'updated_at'])

    label = incident.get_status_display_label()
    add_timeline_event(
        incident,
        _status_timeline_event(new_status),
        f'Status changed to {label}',
        actor=actor,
        description=f'Previous status: {old_status}',
        metadata={'old_status': old_status, 'new_status': new_status},
    )

    if incident.user_id:
        Notification.objects.create(
            user_id=incident.user_id,
            title='Incident status updated',
            message=f'Your report {incident.report_id[:8]}… is now: {label}.',
            notification_type='report_update',
            related_report=incident,
        )

    try:
        from projdjango.emails import send_incident_status_email
        send_incident_status_email(incident, old_status, new_status)
    except Exception:
        pass

    return incident


def assign_officer(incident, officer, assigned_by, notes='', request=None):
    """Assign or reassign officer with full history."""
    previous = incident.assigned_officer
    if previous and previous.id == (officer.id if officer else None):
        return incident

    CaseAssignment.objects.filter(incident=incident, is_active=True).update(
        is_active=False,
        unassigned_at=timezone.now(),
    )

    if officer:
        CaseAssignment.objects.create(
            incident=incident,
            officer=officer,
            assigned_by=assigned_by,
            notes=notes,
            is_active=True,
        )
        incident.assigned_officer = officer
        event = 'reassigned' if previous else 'assigned'
        officer_name = officer.get_full_name() or officer.username
        add_timeline_event(
            incident,
            event,
            f'Assigned to {officer_name}',
            actor=assigned_by,
            description=notes,
            metadata={'officer_id': officer.id},
        )
        if incident.user_id:
            Notification.objects.create(
                user_id=incident.user_id,
                title='Officer assigned to your case',
                message=f'An officer has been assigned to report {incident.report_id[:8]}….',
                notification_type='report_update',
                related_report=incident,
            )
        try:
            from projdjango.emails import send_incident_assigned_email
            send_incident_assigned_email(incident, officer)
        except Exception:
            pass
    else:
        incident.assigned_officer = None
        add_timeline_event(
            incident,
            'reassigned',
            'Officer unassigned',
            actor=assigned_by,
            description=notes,
        )

    incident.save(update_fields=['assigned_officer', 'updated_at'])
    return incident


def validate_evidence_file(uploaded_file):
    """Validate file type and size. Returns (ok, error_message)."""
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 52_428_800)
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in Evidence.ALLOWED_EXTENSIONS:
        return False, f'File type {ext} is not allowed.'
    if uploaded_file.size > max_size:
        return False, f'File exceeds maximum size of {max_size // (1024 * 1024)} MB.'
    return True, ''


def upload_evidence(incident, uploaded_file, *, category='other', description='', uploaded_by=None):
    """Save evidence file with validation and timeline entry."""
    ok, err = validate_evidence_file(uploaded_file)
    if not ok:
        raise ValueError(err)

    evidence = Evidence.objects.create(
        incident=incident,
        file=uploaded_file,
        original_filename=uploaded_file.name,
        category=category,
        description=description,
        uploaded_by=uploaded_by,
        file_size=uploaded_file.size,
    )

    add_timeline_event(
        incident,
        'evidence_uploaded',
        f'Evidence uploaded: {uploaded_file.name}',
        actor=uploaded_by,
        description=description,
        metadata={'evidence_id': evidence.id, 'category': category},
    )

    if incident.user_id:
        Notification.objects.create(
            user_id=incident.user_id,
            title='New evidence on your case',
            message=f'Evidence was added to report {incident.report_id[:8]}….',
            notification_type='report_update',
            related_report=incident,
        )

    return evidence


def get_officer_workload():
    """Return queryset of staff with active assignment counts."""
    from django.contrib.auth.models import User
    from django.db.models import Count, Q

    return (
        User.objects.filter(is_staff=True, is_active=True)
        .annotate(
            active_cases=Count(
                'case_assignments',
                filter=Q(case_assignments__is_active=True),
            ),
            pending_cases=Count(
                'assigned_incidents',
                filter=Q(assigned_incidents__status='submitted'),
            ),
            review_cases=Count(
                'assigned_incidents',
                filter=Q(assigned_incidents__status='under_review'),
            ),
        )
        .order_by('-active_cases', 'first_name')
    )


def seed_initial_timeline(incident):
    """Create submitted timeline event if none exist (for legacy reports)."""
    if not incident.timeline_events.exists():
        add_timeline_event(
            incident,
            'submitted',
            'Report submitted',
            description='Incident report received by the system.',
            metadata={'report_id': incident.report_id},
        )
