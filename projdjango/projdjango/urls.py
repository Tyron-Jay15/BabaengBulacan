from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from .views import (
    home_view,
    about_view,
    faq_view,
    privacy_view,
    terms_view,
    programs_view,
    ResourceCenterView,
    ContactView,
    track_case_view,
    report_success_view,
    IncidentReportView,
    incident_report_view,
    get_captcha_challenge,
    ChatbotPageView,
    ChatbotAPIView,
    ChatbotHistoryView,
)
from projdjango.admin import security_dashboard
from projdjango.pwa_views import web_manifest, service_worker

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('admin/security-dashboard/', security_dashboard, name='security_dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('projdjango.accounts_urls')),
    path('about/', about_view, name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('resources/', ResourceCenterView.as_view(), name='resources'),
    path('programs/', programs_view, name='programs'),
    path('faq/', faq_view, name='faq'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
    path('home/', home_view, name='home'),
    path('anonymous-report/', IncidentReportView.as_view(), name='anonymous_report'),
    path('incident-report/', incident_report_view, name='incident_report'),
    path('track-case/', track_case_view, name='track_case'),
    path('report-success/', report_success_view, name='report_success'),
    path('manifest.webmanifest', web_manifest, name='web_manifest'),
    path('manifest.json', web_manifest, name='manifest_json'),
    path('sw.js', service_worker, name='service_worker'),
    path('api/', include('projdjango.api.urls')),
    path('api/captcha/', get_captcha_challenge, name='get_captcha'),
    path('api/chatbot/message/', ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/chatbot/history/', ChatbotHistoryView.as_view(), name='chatbot_history'),
    path('chatbot/', ChatbotPageView.as_view(), name='chatbot'),
    path('search/', include('projdjango.search.urls')),
    path('dashboard/', include('projdjango.user_dashboard.urls')),
    path('admin-dashboard/', include('projdjango.admin_dashboard.urls')),
    # Legacy URL aliases used by older templates/docs
    path('cases/dashboard/', RedirectView.as_view(url='/dashboard/', permanent=False), name='dashboard'),
    path('reports/incident/', RedirectView.as_view(url='/incident-report/', permanent=False)),
    path('reports/anonymous/', RedirectView.as_view(url='/anonymous-report/', permanent=False)),
    path('reports/track/', RedirectView.as_view(url='/track-case/', permanent=False)),
    path('reports/success/', RedirectView.as_view(url='/report-success/', permanent=False)),
    path('accounts/bluetooth-login/', RedirectView.as_view(url='/accounts/login/', permanent=False)),
]

# Serve user uploads locally during development only.
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
