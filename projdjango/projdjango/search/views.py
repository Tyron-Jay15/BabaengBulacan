"""
Search & Filter views for BabaengBulacan (Activity 10).

Each view:
  1. Reads GET parameters (search q + filters)
  2. Delegates QuerySet building to search.services
  3. Paginates results (5 per page via settings.SEARCH_PAGE_SIZE)
  4. Renders a template with search bar, filters, table/cards, pagination
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.utils.http import urlencode

from .services import (
    search_incidents,
    search_users,
    search_announcements,
    search_barangays,
    search_municipalities,
    search_auth_logs,
    search_notifications,
    get_filter_options,
)


def _paginate(queryset, request, param_name='page'):
    """Paginate a QuerySet; return (page_obj, paginator)."""
    per_page = getattr(settings, 'SEARCH_PAGE_SIZE', 5)
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(param_name, 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


def _query_string(request, exclude=('page',)):
    """Build a query string preserving current filters but excluding given keys."""
    params = [(k, v) for k, v in request.GET.items() if k not in exclude and v]
    return urlencode(params)


def _staff_required(user):
    return user.is_authenticated and user.is_staff


# ---------------------------------------------------------------------------
# Hub – links to all searchable modules
# ---------------------------------------------------------------------------
@login_required(login_url='admin_login')
@user_passes_test(_staff_required, login_url='admin_login')
def search_hub(request):
    """Admin hub listing all searchable modules."""
    modules = [
        {'title': 'Incident Reports', 'desc': 'Search by reporter, type, barangay; filter by status and date.', 'url': 'search_incidents', 'icon': 'fa-file-alt'},
        {'title': 'Registered Users', 'desc': 'Search by name or email; filter by role and verification.', 'url': 'search_users', 'icon': 'fa-users'},
        {'title': 'Announcements', 'desc': 'Search titles and content; filter by category and month.', 'url': 'search_announcements', 'icon': 'fa-bullhorn'},
        {'title': 'Barangays', 'desc': 'Search barangay names; filter by municipality.', 'url': 'search_barangays', 'icon': 'fa-map-marker-alt'},
        {'title': 'Municipalities', 'desc': 'Search Bulacan municipalities.', 'url': 'search_municipalities', 'icon': 'fa-city'},
        {'title': 'Authentication Logs', 'desc': 'Audit trail search for admin security review.', 'url': 'search_auth_logs', 'icon': 'fa-shield-alt'},
        {'title': 'Notifications', 'desc': 'Search user notifications and alerts.', 'url': 'search_notifications', 'icon': 'fa-bell'},
    ]
    return render(request, 'search/hub.html', {'modules': modules})


# ---------------------------------------------------------------------------
# Incident Reports
# ---------------------------------------------------------------------------
@login_required(login_url='admin_login')
@user_passes_test(_staff_required, login_url='admin_login')
def incident_search(request):
    qs = search_incidents(request.GET)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/incidents_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        **options,
    })


# ---------------------------------------------------------------------------
# Registered Users
# ---------------------------------------------------------------------------
@login_required(login_url='admin_login')
@user_passes_test(_staff_required, login_url='admin_login')
def user_search(request):
    qs = search_users(request.GET)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/users_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        **options,
    })


# ---------------------------------------------------------------------------
# Announcements (public read; staff sees unpublished too)
# ---------------------------------------------------------------------------
def announcement_search(request):
    staff = request.user.is_authenticated and request.user.is_staff
    qs = search_announcements(request.GET, staff_view=staff)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/announcements_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        'is_staff': staff,
        **options,
    })


# ---------------------------------------------------------------------------
# Barangays & Municipalities
# ---------------------------------------------------------------------------
def barangay_search(request):
    qs = search_barangays(request.GET)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/barangays_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        **options,
    })


def municipality_search(request):
    qs = search_municipalities(request.GET)
    page_obj, paginator = _paginate(qs, request)
    return render(request, 'search/municipalities_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
    })


# ---------------------------------------------------------------------------
# Authentication Logs (Admin)
# ---------------------------------------------------------------------------
@login_required(login_url='admin_login')
@user_passes_test(_staff_required, login_url='admin_login')
def auth_log_search(request):
    qs = search_auth_logs(request.GET)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/auth_logs_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        **options,
    })


# ---------------------------------------------------------------------------
# Notifications (Optional – login required)
# ---------------------------------------------------------------------------
@login_required
def notification_search(request):
    staff = request.user.is_staff
    qs = search_notifications(request.GET, user=request.user, staff_view=staff)
    page_obj, paginator = _paginate(qs, request)
    options = get_filter_options()
    return render(request, 'search/notifications_list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'query_string': _query_string(request),
        'filters': request.GET,
        'is_staff': staff,
        **options,
    })
