from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('analytics/', views.analytics, name='admin_analytics'),
    path('activity-logs/', views.activity_logs, name='admin_activity_logs'),
    path('officer-workload/', views.officer_workload, name='admin_officer_workload'),
    path('backend/', views.backend_hub, name='admin_backend'),
    path('incidents/<str:report_id>/', views.incident_detail, name='admin_incident_detail'),
    path('incidents/<str:report_id>/edit/', views.incident_edit, name='admin_incident_edit'),
    path('incidents/<str:report_id>/status/', views.incident_update_status, name='admin_incident_status'),
    path('incidents/<str:report_id>/evidence/', views.incident_upload_evidence, name='admin_incident_evidence'),
    path('users/<int:user_id>/verify-email/', views.verify_user_email, name='admin_verify_user_email'),
    path('users/<int:user_id>/delete/', views.delete_user, name='admin_delete_user'),
]
