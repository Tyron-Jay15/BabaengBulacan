"""
Search & Filter services for BabaengBulacan (Activity 10).

Centralises QuerySet construction: search (Q + icontains), filters, ordering,
and ORM optimisations (select_related, prefetch_related, only, defer).

Each function accepts a dict-like params object (typically request.GET) and
returns an unevaluated, lazy QuerySet ready for Django Paginator.
"""
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Q, BooleanField, Case, When, Value
from django.utils import timezone
from django.utils.dateparse import parse_date

from projdjango.models import (
    IncidentReport, Announcement, Municipality, Barangay,
    Notification, AuthenticationLog, UserProfile,
)


def _clean(value):
    """Strip whitespace from a GET parameter value."""
    if value is None:
        return ''
    return str(value).strip()


def _parse_month_year(month_str, year_str):
    """Return (start, end) datetimes for a calendar month filter, or (None, None)."""
    try:
        month = int(month_str)
        year = int(year_str) if year_str else timezone.now().year
        if not 1 <= month <= 12:
            return None, None
        start = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end = timezone.make_aware(datetime(year, month + 1, 1))
        return start, end
    except (TypeError, ValueError):
        return None, None


# ---------------------------------------------------------------------------
# Incident Reports
# ---------------------------------------------------------------------------
def search_incidents(params):
    """
    Build an optimised QuerySet for incident report search & filter.

    Search (q): reporter name, incident type, location, barangay, municipality, report_id
    Filters: status, incident_type, barangay, municipality, date_from, date_to, include_archived
    """
    qs = (
        IncidentReport.objects
        .select_related('barangay', 'barangay__municipality', 'assigned_officer')
        .only(
            'id', 'report_id', 'full_name', 'email', 'contact_number',
            'incident_type', 'incident_description', 'incident_location',
            'incident_date', 'status', 'created_at', 'updated_at', 'is_archived',
            'barangay_id', 'assigned_officer_id',
            'barangay__name', 'barangay__municipality_id',
            'barangay__municipality__name',
            'assigned_officer__username', 'assigned_officer__first_name',
            'assigned_officer__last_name',
        )
        .order_by('-created_at')
    )

    if _clean(params.get('include_archived')) != '1':
        qs = qs.filter(is_archived=False)

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q)
            | Q(incident_type__icontains=q)
            | Q(incident_location__icontains=q)
            | Q(report_id__icontains=q)
            | Q(barangay__name__icontains=q)
            | Q(barangay__municipality__name__icontains=q)
            | Q(incident_description__icontains=q)
        )

    status = _clean(params.get('status'))
    if status:
        qs = qs.filter(status=status)

    incident_type = _clean(params.get('incident_type'))
    if incident_type:
        qs = qs.filter(incident_type=incident_type)

    barangay_id = _clean(params.get('barangay'))
    if barangay_id.isdigit():
        qs = qs.filter(barangay_id=int(barangay_id))

    municipality_id = _clean(params.get('municipality'))
    if municipality_id.isdigit():
        qs = qs.filter(barangay__municipality_id=int(municipality_id))

    date_from = _clean(params.get('date_from'))
    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            qs = qs.filter(created_at__date__gte=parsed)

    date_to = _clean(params.get('date_to'))
    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            qs = qs.filter(created_at__date__lte=parsed)

    return qs


# ---------------------------------------------------------------------------
# Registered Users
# ---------------------------------------------------------------------------
def search_users(params):
    """
    Build QuerySet for registered user search & filter.

    Search (q): name, email, username
    Filters: role, verified, account_status
    """
    qs = (
        User.objects
        .select_related('userprofile')
        .only(
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'userprofile__email_verified', 'userprofile__lockout_until',
            'userprofile__login_attempts', 'userprofile__face_photo',
        )
        .order_by('-date_joined')
    )
    qs = qs.annotate(
        face_enrolled=Case(
            When(userprofile__face_encoding__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    )

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(username__icontains=q)
        )

    role = _clean(params.get('role'))
    if role == 'super_admin':
        qs = qs.filter(is_superuser=True)
    elif role == 'admin':
        qs = qs.filter(is_staff=True, is_superuser=False)
    elif role == 'resident':
        qs = qs.filter(is_staff=False, is_superuser=False)

    verified = _clean(params.get('verified'))
    if verified == 'yes':
        qs = qs.filter(userprofile__email_verified=True)
    elif verified == 'no':
        qs = qs.filter(userprofile__email_verified=False)

    account_status = _clean(params.get('account_status'))
    now = timezone.now()
    if account_status == 'active':
        qs = qs.filter(is_active=True).exclude(
            userprofile__lockout_until__gt=now,
        )
    elif account_status == 'inactive':
        qs = qs.filter(is_active=False)
    elif account_status == 'locked':
        qs = qs.filter(userprofile__lockout_until__gt=now)

    return qs


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------
def search_announcements(params, *, staff_view=False):
    """
    Search announcements by title/description; filter by category and date.

    Non-staff callers only see published announcements.
    """
    qs = (
        Announcement.objects
        .select_related('posted_by')
        .only(
            'id', 'title', 'description', 'category', 'is_published', 'is_archived',
            'created_at', 'updated_at', 'posted_by_id',
            'posted_by__username', 'posted_by__first_name', 'posted_by__last_name',
        )
        .order_by('-created_at')
    )

    if not staff_view:
        qs = qs.filter(is_published=True)

    if _clean(params.get('include_archived')) != '1':
        qs = qs.filter(is_archived=False)

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )

    category = _clean(params.get('category'))
    if category:
        qs = qs.filter(category=category)

    month = _clean(params.get('month'))
    year = _clean(params.get('year'))
    if month.isdigit():
        start, end = _parse_month_year(month, year)
        if start and end:
            qs = qs.filter(created_at__gte=start, created_at__lt=end)

    date_from = _clean(params.get('date_from'))
    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            qs = qs.filter(created_at__date__gte=parsed)

    return qs


# ---------------------------------------------------------------------------
# Barangays & Municipalities
# ---------------------------------------------------------------------------
def search_barangays(params):
    """Search barangays by name; filter by municipality."""
    qs = (
        Barangay.objects
        .select_related('municipality')
        .only('id', 'name', 'is_active', 'created_at', 'municipality_id', 'municipality__name')
        .filter(is_active=True)
        .order_by('municipality__name', 'name')
    )

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(municipality__name__icontains=q)
        )

    municipality_id = _clean(params.get('municipality'))
    if municipality_id.isdigit():
        qs = qs.filter(municipality_id=int(municipality_id))

    return qs


def search_municipalities(params):
    """Search municipalities by name or province."""
    from django.db.models import Count
    qs = (
        Municipality.objects
        .annotate(barangay_count=Count('barangays'))
        .only('id', 'name', 'province', 'is_active', 'created_at')
        .filter(is_active=True)
        .order_by('name')
    )

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(province__icontains=q)
        )

    return qs


# ---------------------------------------------------------------------------
# Authentication Logs (Admin)
# ---------------------------------------------------------------------------
def search_auth_logs(params):
    """Search authentication audit logs; filter by event type and success."""
    qs = (
        AuthenticationLog.objects
        .select_related('user')
        .only(
            'id', 'event_type', 'username_attempted', 'auth_method', 'success',
            'ip_address', 'device', 'browser', 'os', 'details', 'created_at',
            'user_id', 'user__username',
        )
        .order_by('-created_at')
    )

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(
            Q(username_attempted__icontains=q)
            | Q(user__username__icontains=q)
            | Q(ip_address__icontains=q)
            | Q(details__icontains=q)
            | Q(device__icontains=q)
        )

    event_type = _clean(params.get('event_type'))
    if event_type:
        qs = qs.filter(event_type=event_type)

    success = _clean(params.get('success'))
    if success == 'yes':
        qs = qs.filter(success=True)
    elif success == 'no':
        qs = qs.filter(success=False)

    date_from = _clean(params.get('date_from'))
    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            qs = qs.filter(created_at__date__gte=parsed)

    return qs


# ---------------------------------------------------------------------------
# Notifications (Optional)
# ---------------------------------------------------------------------------
def search_notifications(params, user=None, staff_view=False):
    """Search notifications for the current user (staff sees all)."""
    qs = (
        Notification.objects
        .select_related('user', 'related_report')
        .only(
            'id', 'title', 'message', 'notification_type', 'is_read',
            'created_at', 'user_id', 'related_report_id',
            'user__username', 'related_report__report_id',
        )
        .order_by('-created_at')
    )

    if staff_view:
        pass  # all notifications
    elif user and user.is_authenticated:
        qs = qs.filter(user=user)
    else:
        return qs.none()

    q = _clean(params.get('q'))
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(message__icontains=q))

    notification_type = _clean(params.get('notification_type'))
    if notification_type:
        qs = qs.filter(notification_type=notification_type)

    is_read = _clean(params.get('is_read'))
    if is_read == 'yes':
        qs = qs.filter(is_read=True)
    elif is_read == 'no':
        qs = qs.filter(is_read=False)

    return qs


# ---------------------------------------------------------------------------
# Filter dropdown helpers (for templates)
# ---------------------------------------------------------------------------
def get_filter_options():
    """Return choice lists used by search form dropdowns."""
    return {
        'incident_statuses': IncidentReport.STATUS_CHOICES,
        'incident_types': IncidentReport.INCIDENT_TYPE_CHOICES,
        'barangays': Barangay.objects.select_related('municipality').filter(is_active=True).order_by('name'),
        'municipalities': Municipality.objects.filter(is_active=True).order_by('name'),
        'announcement_categories': Announcement.CATEGORY_CHOICES,
        'auth_event_types': AuthenticationLog.EVENT_CHOICES,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'user_roles': [
            ('resident', 'Resident'),
            ('admin', 'Admin'),
            ('super_admin', 'Super Admin'),
        ],
        'verified_choices': [('yes', 'Verified'), ('no', 'Unverified')],
        'account_status_choices': [
            ('active', 'Active'),
            ('locked', 'Locked'),
            ('inactive', 'Inactive'),
        ],
    }
