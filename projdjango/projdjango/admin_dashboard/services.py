"""Dashboard statistics and helpers for the Admin Dashboard."""
from django.contrib.auth.models import User
from django.db.models import Count, Q

from projdjango.models import Announcement, IncidentReport, UserProfile


def get_dashboard_stats():
    """
    Aggregate KPI counts for the admin dashboard summary cards.
    Uses efficient count queries — no full table scans into memory.
    """
    total_users = User.objects.count()
    verified_users = UserProfile.objects.filter(email_verified=True).count()
    unverified_users = UserProfile.objects.filter(email_verified=False).count()

    incident_counts = (
        IncidentReport.objects
        .aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='submitted')),
            ongoing=Count('id', filter=Q(status='under_review')),
            resolved=Count('id', filter=Q(status='resolved')),
        )
    )

    return {
        'total_users': total_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'total_incidents': incident_counts['total'],
        'pending_reports': incident_counts['pending'],
        'ongoing_reports': incident_counts['ongoing'],
        'resolved_reports': incident_counts['resolved'],
        'total_announcements': Announcement.objects.count(),
    }


def prefix_params(request_get, prefix, field_map):
    """
    Map prefixed GET params to the keys expected by search.services.

    Example: inc_q -> q, inc_status -> status
    """
    params = {}
    for prefixed_key, service_key in field_map.items():
        value = request_get.get(prefixed_key, '')
        if value:
            params[service_key] = value
    return params


def get_analytics_data():
    """Build Chart.js datasets from live database aggregates."""
    import json
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from django.utils import timezone

    from projdjango.models import Barangay, IncidentReport

    active = IncidentReport.objects.filter(is_archived=False)

    by_type = list(
        active.values('incident_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    by_status = list(
        active.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    by_municipality = list(
        active.filter(barangay__isnull=False)
        .values('barangay__municipality__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    by_barangay = list(
        active.filter(barangay__isnull=False)
        .values('barangay__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly = list(
        active.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    total = active.count()
    resolved = active.filter(status='resolved').count()
    resolution_rate = round((resolved / total * 100), 1) if total else 0

    return {
        'by_type_labels': json.dumps([r['incident_type'].title() for r in by_type]),
        'by_type_data': json.dumps([r['count'] for r in by_type]),
        'by_status_labels': json.dumps([r['status'].replace('_', ' ').title() for r in by_status]),
        'by_status_data': json.dumps([r['count'] for r in by_status]),
        'muni_labels': json.dumps([r['barangay__municipality__name'] for r in by_municipality]),
        'muni_data': json.dumps([r['count'] for r in by_municipality]),
        'brgy_labels': json.dumps([r['barangay__name'] for r in by_barangay]),
        'brgy_data': json.dumps([r['count'] for r in by_barangay]),
        'monthly_labels': json.dumps([
            r['month'].strftime('%b %Y') if r['month'] else '' for r in monthly
        ]),
        'monthly_data': json.dumps([r['count'] for r in monthly]),
        'resolution_rate': resolution_rate,
        'total_incidents': total,
    }
