"""
URL routes for the Search & Filter module (Activity 10).

Mounted at /search/ in the main project urls.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_hub, name='search_hub'),
    path('incidents/', views.incident_search, name='search_incidents'),
    path('users/', views.user_search, name='search_users'),
    path('announcements/', views.announcement_search, name='search_announcements'),
    path('barangays/', views.barangay_search, name='search_barangays'),
    path('municipalities/', views.municipality_search, name='search_municipalities'),
    path('auth-logs/', views.auth_log_search, name='search_auth_logs'),
    path('notifications/', views.notification_search, name='search_notifications'),
]
