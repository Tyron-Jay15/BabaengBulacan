"""
DRF API Views for BabaengBulacan (Activity 9).

Uses ViewSets + DefaultRouter — the recommended DRF pattern for this project
because it auto-generates list/detail routes, supports GET and POST cleanly,
and scales when adding mobile clients later.
"""
from django.contrib.auth.models import User
from rest_framework import viewsets, mixins, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from projdjango.models import (
    IncidentReport, Announcement, Municipality, Barangay,
    Notification, AuthenticationLog,
)
from .serializers import (
    UserAPISerializer,
    IncidentReportAPISerializer,
    IncidentReportCreateSerializer,
    AnnouncementAPISerializer,
    AnnouncementCreateSerializer,
    MunicipalityAPISerializer,
    BarangayAPISerializer,
    NotificationAPISerializer,
    AuthenticationLogAPISerializer,
)
from .permissions import IsStaffOrReadOnly, IsAdminOrReadOnly


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/users/          → list all registered users
    GET /api/users/{id}/     → single user detail

    Search: ?search=maria   Filter: (via client-side role from serializer)
    """
    queryset = User.objects.select_related('userprofile').order_by('-date_joined')
    serializer_class = UserAPISerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['date_joined', 'email']


class IncidentReportViewSet(viewsets.ModelViewSet):
    """
    GET  /api/incidents/         → list incident reports
    GET  /api/incidents/{id}/    → single report
    POST /api/incidents/         → submit a new report (authenticated or anonymous)

    Query params: ?status=submitted  ?incident_type=violence
    """
    queryset = IncidentReport.objects.select_related(
        'barangay', 'barangay__municipality', 'assigned_officer',
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'incident_type', 'barangay', 'barangay__municipality']
    search_fields = [
        'full_name', 'incident_type', 'incident_location', 'report_id',
        'barangay__name', 'barangay__municipality__name', 'incident_description',
    ]
    ordering_fields = ['created_at', 'status']

    def get_permissions(self):
        if self.action == 'create':
            # Anyone can submit an incident report (matches the web form)
            return [AllowAny()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsStaffOrReadOnly()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentReportCreateSerializer
        return IncidentReportAPISerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return the read serializer shape so POST response matches GET format
        output = IncidentReportAPISerializer(serializer.instance, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    GET  /api/announcements/         → list published announcements
    GET  /api/announcements/{id}/    → single announcement
    POST /api/announcements/         → create (staff only)
    """
    serializer_class = AnnouncementAPISerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_published']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_queryset(self):
        qs = Announcement.objects.select_related('posted_by').order_by('-created_at')
        # Non-staff users only see published announcements
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return AnnouncementCreateSerializer
        return AnnouncementAPISerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = AnnouncementAPISerializer(serializer.instance, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class MunicipalityViewSet(viewsets.ModelViewSet):
    """GET/POST /api/municipalities/ — Bulacan municipality management."""
    queryset = Municipality.objects.filter(is_active=True).order_by('name')
    serializer_class = MunicipalityAPISerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'province']


class BarangayViewSet(viewsets.ModelViewSet):
    """GET/POST /api/barangays/ — barangays under municipalities."""
    queryset = Barangay.objects.select_related('municipality').filter(is_active=True).order_by('name')
    serializer_class = BarangayAPISerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['municipality']
    search_fields = ['name', 'municipality__name']


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
    """
    GET  /api/notifications/       → current user's notifications (staff: all)
    GET  /api/notifications/{id}/  → single notification
    POST /api/notifications/       → create (staff only)
    POST /api/notifications/{id}/mark_read/ → mark as read
    """
    serializer_class = NotificationAPISerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.select_related('user', 'related_report').order_by('-created_at')
        if self.request.user and self.request.user.is_staff:
            return qs
        if self.request.user and self.request.user.is_authenticated:
            return qs.filter(user=self.request.user)
        return qs.none()

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationAPISerializer(notification).data)


class AuthenticationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/auth-logs/ — authentication audit trail (staff only).
    """
    queryset = AuthenticationLog.objects.select_related('user').order_by('-created_at')
    serializer_class = AuthenticationLogAPISerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'success', 'user']
    search_fields = ['username_attempted', 'user__username', 'ip_address', 'details', 'device']
    ordering_fields = ['created_at']
