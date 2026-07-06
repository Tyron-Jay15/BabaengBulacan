"""
API URL routing for BabaengBulacan (Activity 9).

Registered in the main project urls.py as:
    path('api/', include('projdjango.api.urls')),

Generated endpoints (via DefaultRouter):
    /api/users/
    /api/incidents/
    /api/announcements/
    /api/municipalities/       (optional)
    /api/barangays/            (optional)
    /api/notifications/        (optional)
    /api/auth-logs/            (optional)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    IncidentReportViewSet,
    AnnouncementViewSet,
    MunicipalityViewSet,
    BarangayViewSet,
    NotificationViewSet,
    AuthenticationLogViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='api-user')
router.register(r'incidents', IncidentReportViewSet, basename='api-incident')
router.register(r'announcements', AnnouncementViewSet, basename='api-announcement')
router.register(r'municipalities', MunicipalityViewSet, basename='api-municipality')
router.register(r'barangays', BarangayViewSet, basename='api-barangay')
router.register(r'notifications', NotificationViewSet, basename='api-notification')
router.register(r'auth-logs', AuthenticationLogViewSet, basename='api-auth-log')

urlpatterns = [
    path('', include(router.urls)),
]
