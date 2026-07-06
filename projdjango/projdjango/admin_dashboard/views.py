"""Admin Dashboard views — staff-only management hub (Activity 10)."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from projdjango import emails as auth_emails
from projdjango.audit.services import log_action
from projdjango.case_management.services import (
    assign_officer,
    get_officer_workload,
    record_status_change,
    seed_initial_timeline,
    upload_evidence,
    validate_evidence_file,
)
from projdjango.models import AuditLog, IncidentReport, UserProfile
from projdjango.search.services import (
    get_filter_options,
    search_announcements,
    search_incidents,
    search_users,
)

from .admin_links import get_django_admin_sections
from .services import get_analytics_data, get_dashboard_stats, prefix_params


def _staff_required(user):
    return user.is_authenticated and user.is_staff


def staff_admin_required(view_func):
    """Decorator: staff login portal + staff only."""
    @login_required(login_url='admin_login')
    def wrapper(request, *args, **kwargs):
        if not _staff_required(request.user):
            messages.error(request, 'Access denied. Administrator privileges are required.')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def _paginate(queryset, request, page_param='page', per_page=None):
    per_page = per_page or getattr(settings, 'SEARCH_PAGE_SIZE', 5)
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param, 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


def _query_string(request, prefix, fields, exclude=('page',)):
    """Build query string preserving prefixed filter params."""
    params = []
    for key in fields:
        val = request.GET.get(key, '')
        if val and key not in exclude:
            params.append((key, val))
    page_key = f'{prefix}_page'
    if page_key not in exclude and request.GET.get(page_key):
        pass  # page handled separately by caller
    return urlencode(params)


INCIDENT_FIELDS = {
    'inc_q': 'q', 'inc_status': 'status', 'inc_type': 'incident_type',
    'inc_barangay': 'barangay', 'inc_municipality': 'municipality',
    'inc_date_from': 'date_from', 'inc_date_to': 'date_to',
}
USER_FIELDS = {
    'usr_q': 'q', 'usr_role': 'role', 'usr_verified': 'verified',
    'usr_status': 'account_status',
}
ANNOUNCEMENT_FIELDS = {
    'ann_q': 'q', 'ann_category': 'category', 'ann_month': 'month',
    'ann_year': 'year',
}


@staff_admin_required
def dashboard(request):
    """Main admin dashboard with KPI cards and three management sections."""
    stats = get_dashboard_stats()
    options = get_filter_options()

    inc_params = prefix_params(request.GET, 'inc', INCIDENT_FIELDS)
    inc_qs = search_incidents(inc_params)
    inc_page, inc_paginator = _paginate(inc_qs, request, page_param='inc_page')

    usr_params = prefix_params(request.GET, 'usr', USER_FIELDS)
    usr_qs = search_users(usr_params)
    usr_page, usr_paginator = _paginate(usr_qs, request, page_param='usr_page')

    ann_params = prefix_params(request.GET, 'ann', ANNOUNCEMENT_FIELDS)
    ann_qs = search_announcements(ann_params, staff_view=True)
    ann_page, ann_paginator = _paginate(ann_qs, request, page_param='ann_page')

    staff_officers = (
        User.objects.filter(is_staff=True, is_active=True)
        .only('id', 'username', 'first_name', 'last_name')
        .order_by('first_name', 'username')
    )

    context = {
        'stats': stats,
        'inc_page': inc_page,
        'inc_paginator': inc_paginator,
        'inc_total': inc_paginator.count,
        'inc_filters': request.GET,
        'inc_query_string': _query_string(request, 'inc', INCIDENT_FIELDS.keys(), exclude=('inc_page',)),
        'usr_page': usr_page,
        'usr_paginator': usr_paginator,
        'usr_total': usr_paginator.count,
        'usr_filters': request.GET,
        'usr_query_string': _query_string(request, 'usr', USER_FIELDS.keys(), exclude=('usr_page',)),
        'ann_page': ann_page,
        'ann_paginator': ann_paginator,
        'ann_total': ann_paginator.count,
        'ann_filters': request.GET,
        'ann_query_string': _query_string(request, 'ann', ANNOUNCEMENT_FIELDS.keys(), exclude=('ann_page',)),
        'staff_officers': staff_officers,
        **options,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@staff_admin_required
def incident_detail(request, report_id):
    """View full incident report details with timeline and evidence."""
    incident = get_object_or_404(
        IncidentReport.objects.select_related(
            'barangay', 'barangay__municipality', 'assigned_officer', 'user',
        ).prefetch_related('timeline_events', 'evidence_items', 'assignment_history'),
        report_id=report_id,
    )
    seed_initial_timeline(incident)
    timeline = incident.timeline_events.select_related('actor').all()
    evidence = incident.evidence_items.select_related('uploaded_by').all()
    assignments = incident.assignment_history.select_related('officer', 'assigned_by').all()
    return render(request, 'admin_dashboard/incident_detail.html', {
        'incident': incident,
        'timeline': timeline,
        'evidence_items': evidence,
        'assignments': assignments,
    })


@staff_admin_required
def incident_edit(request, report_id):
    """Edit incident status and assigned officer."""
    incident = get_object_or_404(
        IncidentReport.objects.select_related('barangay', 'assigned_officer'),
        report_id=report_id,
    )
    staff_officers = (
        User.objects.filter(is_staff=True, is_active=True)
        .only('id', 'username', 'first_name', 'last_name')
        .order_by('first_name', 'username')
    )

    if request.method == 'POST':
        old_status = incident.status
        status = request.POST.get('status', incident.status)
        officer_id = request.POST.get('assigned_officer', '')
        notes = request.POST.get('notes', '').strip()

        old_officer_id = incident.assigned_officer_id
        officer = None
        if officer_id.isdigit():
            officer = User.objects.filter(id=int(officer_id), is_staff=True).first()

        if status in dict(IncidentReport.STATUS_CHOICES) and status != old_status:
            record_status_change(incident, old_status, status, request.user, request)
            log_action(request, 'status_changed', object_type='IncidentReport',
                       object_id=incident.report_id, details=f'{old_status} → {status}')

        assign_officer(incident, officer, request.user, notes=notes, request=request)
        if officer and officer.id != old_officer_id:
            log_action(request, 'case_assigned', object_type='IncidentReport',
                       object_id=incident.report_id, details=f'Assigned to {officer.username}')

        incident.refresh_from_db()
        messages.success(request, f'Report {incident.report_id[:8]}… updated successfully.')
        return redirect('admin_incident_detail', report_id=incident.report_id)

    return render(request, 'admin_dashboard/incident_edit.html', {
        'incident': incident,
        'staff_officers': staff_officers,
        'status_choices': IncidentReport.STATUS_CHOICES,
    })


@staff_admin_required
@require_POST
def incident_update_status(request, report_id):
    """Quick status update from the dashboard table."""
    incident = get_object_or_404(IncidentReport, report_id=report_id)
    status = request.POST.get('status', '')
    valid = dict(IncidentReport.STATUS_CHOICES)
    if status in valid:
        old = incident.status
        record_status_change(incident, old, status, request.user, request)
        log_action(request, 'status_changed', object_type='IncidentReport',
                   object_id=incident.report_id, details=f'{old} → {status}')
        messages.success(request, f'Status updated to {valid[status]}.')
    else:
        messages.error(request, 'Invalid status selected.')
    return redirect(request.META.get('HTTP_REFERER') or reverse('admin_dashboard'))


@staff_admin_required
@require_POST
def incident_upload_evidence(request, report_id):
    """Upload evidence file for an incident."""
    incident = get_object_or_404(IncidentReport, report_id=report_id)
    uploaded = request.FILES.get('evidence_file')
    if not uploaded:
        messages.error(request, 'Please select a file to upload.')
        return redirect('admin_incident_detail', report_id=report_id)

    ok, err = validate_evidence_file(uploaded)
    if not ok:
        messages.error(request, err)
        return redirect('admin_incident_detail', report_id=report_id)

    try:
        upload_evidence(
            incident, uploaded,
            category=request.POST.get('category', 'other'),
            description=request.POST.get('description', ''),
            uploaded_by=request.user,
        )
        log_action(request, 'evidence_uploaded', object_type='IncidentReport',
                   object_id=incident.report_id, details=uploaded.name)
        messages.success(request, 'Evidence uploaded successfully.')
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect('admin_incident_detail', report_id=report_id)


@staff_admin_required
def activity_logs(request):
    """Administrator activity log with search, filter, pagination."""
    qs = AuditLog.objects.select_related('user').only(
        'id', 'action', 'object_type', 'object_id', 'ip_address', 'browser',
        'details', 'created_at', 'user_id', 'user__username', 'user__first_name', 'user__last_name',
    )

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(details__icontains=q) | Q(object_id__icontains=q)
            | Q(user__username__icontains=q) | Q(user__first_name__icontains=q)
        )
    action = request.GET.get('action', '').strip()
    if action:
        qs = qs.filter(action=action)

    page_obj, paginator = _paginate(qs, request, page_param='page')
    return render(request, 'admin_dashboard/activity_logs.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'filters': request.GET,
        'action_choices': AuditLog.ACTION_CHOICES,
    })


@staff_admin_required
def analytics(request):
    """Chart.js analytics dashboard with live database aggregates."""
    data = get_analytics_data()
    return render(request, 'admin_dashboard/analytics.html', {'charts': data})


@staff_admin_required
def officer_workload(request):
    """Officer assignment workload overview."""
    officers = get_officer_workload()
    return render(request, 'admin_dashboard/officer_workload.html', {'officers': officers})


@staff_admin_required
@require_POST
def verify_user_email(request, user_id):
    """Manually mark a user's email as verified (e.g. when SMTP is unavailable)."""
    target = get_object_or_404(User, pk=user_id)
    redirect_to = request.META.get('HTTP_REFERER') or reverse('admin_dashboard') + '#users'

    profile, _ = UserProfile.objects.get_or_create(user=target)
    if profile.email_verified:
        messages.info(request, f'{target.email} is already verified.')
        return redirect(redirect_to)

    profile.mark_email_verified()
    auth_emails.send_email_verified_notification(target)
    log_action(
        request, 'user_updated',
        object_type='User',
        object_id=str(target.id),
        details=f'Admin approved account for {target.email}',
    )
    messages.success(request, f'Account approved for {target.email}. They can now sign in.')
    return redirect(redirect_to)


@staff_admin_required
@require_POST
def delete_user(request, user_id):
    """Permanently delete a spam or unwanted resident account (staff-only)."""
    target = get_object_or_404(User, pk=user_id)
    redirect_to = request.META.get('HTTP_REFERER') or reverse('admin_dashboard') + '#users'

    if target.id == request.user.id:
        messages.error(request, 'You cannot delete your own account while signed in.')
        return redirect(redirect_to)

    if target.is_superuser:
        messages.error(request, 'Superuser accounts cannot be deleted from the dashboard.')
        return redirect(redirect_to)

    if target.is_staff and not request.user.is_superuser:
        messages.error(request, 'Only a superuser can delete staff or admin accounts.')
        return redirect(redirect_to)

    label = target.get_full_name() or target.username
    email = target.email
    target.delete()
    log_action(
        request, 'other',
        object_type='User',
        object_id=str(user_id),
        details=f'Deleted account: {label} ({email})',
    )
    messages.success(request, f'Account "{email}" has been permanently deleted.')
    return redirect(redirect_to)


@staff_admin_required
def backend_hub(request):
    """Hub page with quick links into Django's built-in admin models."""
    sections = get_django_admin_sections(request)
    return render(request, 'admin_dashboard/backend.html', {
        'admin_sections': sections,
    })

