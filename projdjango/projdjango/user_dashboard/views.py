"""Resident / user dashboard views."""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from projdjango.models import Announcement, IncidentReport, Notification


@login_required
def dashboard(request):
    """Resident dashboard — my reports, notifications, quick links."""
    if request.user.is_staff:
        return redirect('admin_dashboard')

    my_reports = (
        IncidentReport.objects
        .filter(user=request.user)
        .select_related('barangay', 'barangay__municipality')
        .only(
            'id', 'report_id', 'incident_type', 'status', 'created_at',
            'barangay__name', 'barangay__municipality__name',
        )
        .order_by('-created_at')[:5]
    )

    report_stats = (
        IncidentReport.objects.filter(user=request.user)
        .aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='submitted')),
            ongoing=Count('id', filter=Q(status='under_review')),
            resolved=Count('id', filter=Q(status='resolved')),
        )
    )

    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False,
    ).count()

    recent_announcements = (
        Announcement.objects.filter(is_published=True)
        .only('id', 'title', 'category', 'created_at')
        .order_by('-created_at')[:3]
    )

    return render(request, 'user_dashboard/dashboard.html', {
        'my_reports': my_reports,
        'report_stats': report_stats,
        'unread_notifications': unread_notifications,
        'recent_announcements': recent_announcements,
    })
