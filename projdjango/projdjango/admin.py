"""
Admin configuration and the Authentication Security Management module.

Provides:
- Rich ModelAdmins for all auth/security models
- Admin actions (unlock accounts, reset 2FA, mark email verified)
- A consolidated security dashboard view (admin/security-dashboard/)
"""
from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    UserProfile, ChatHistory, IncidentReport,
    EmailVerificationToken, PasswordResetToken, TwoFactorAuth, BackupCode,
    AuthenticationLog, FailedLoginAttempt, KnownDevice,
    Municipality, Barangay, Announcement, Notification,
    CaseTimeline, CaseAssignment, Evidence, AuditLog,
    Feedback, FAQItem, AwarenessArticle, BackupHistory,
)


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------
@admin.action(description='Unlock selected accounts')
def unlock_accounts(modeladmin, request, queryset):
    count = 0
    for profile in queryset:
        if profile.lockout_until or profile.login_attempts:
            profile.lockout_until = None
            profile.login_attempts = 0
            profile.save(update_fields=['lockout_until', 'login_attempts'])
            AuthenticationLog.objects.create(
                user=profile.user, event_type='account_unlocked',
                details='Unlocked by admin', success=True,
            )
            count += 1
    messages.success(request, f'{count} account(s) unlocked.')


@admin.action(description='Mark email as verified')
def mark_email_verified(modeladmin, request, queryset):
    count = 0
    for profile in queryset:
        if not profile.email_verified:
            profile.mark_email_verified()
            count += 1
    messages.success(request, f'{count} account(s) marked as verified.')


@admin.action(description='Reset (disable) two-factor authentication')
def reset_two_factor(modeladmin, request, queryset):
    count = 0
    for twofa in queryset:
        twofa.is_enabled = False
        twofa.encrypted_secret = ''
        twofa.confirmed_at = None
        twofa.save()
        BackupCode.objects.filter(user=twofa.user).delete()
        AuthenticationLog.objects.create(
            user=twofa.user, event_type='2fa_reset',
            details='2FA reset by admin', success=True,
        )
        count += 1
    messages.success(request, f'2FA reset for {count} user(s).')


# ---------------------------------------------------------------------------
# ModelAdmins
# ---------------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'face_photo_thumb', 'email_verified', 'is_locked_display', 'login_attempts',
                    'has_2fa', 'device_name', 'last_login_attempt')
    list_filter = ('email_verified',)
    search_fields = ('user__username', 'user__email', 'device_name')
    actions = [unlock_accounts, mark_email_verified]
    readonly_fields = (
        'last_login_attempt', 'session_start_time', 'email_verified_at',
        'face_photo_preview', 'has_registered_face_display',
    )
    fields = (
        'user', 'face_photo', 'face_photo_preview', 'has_registered_face_display',
        'email_verified', 'email_verified_at', 'device_name',
        'login_attempts', 'lockout_until', 'last_login_attempt', 'session_start_time',
    )

    @admin.display(description='Face')
    def face_photo_thumb(self, obj):
        if obj.face_photo:
            return format_html(
                '<img src="{}" alt="" style="height:40px;width:40px;object-fit:cover;border-radius:50%;border:1px solid #ddd;" />',
                obj.face_photo.url,
            )
        if obj.has_registered_face:
            return format_html('<span style="color:#999;">Encoding only</span>')
        return '—'

    @admin.display(description='Registered face')
    def face_photo_preview(self, obj):
        if obj.face_photo:
            return format_html(
                '<img src="{}" alt="Registered face" style="max-height:200px;border-radius:10px;border:1px solid #ddd;" />',
                obj.face_photo.url,
            )
        if obj.has_registered_face:
            return format_html(
                '<span style="color:#666;">Face encoding is on file, but no photo was saved '
                '(account registered before photo storage was enabled).</span>'
            )
        return format_html('<span style="color:#999;">No face registered</span>')

    @admin.display(boolean=True, description='Face enrolled')
    def has_registered_face_display(self, obj):
        return obj.has_registered_face

    @admin.display(boolean=True, description='Locked')
    def is_locked_display(self, obj):
        return obj.is_locked_out()

    @admin.display(boolean=True, description='2FA')
    def has_2fa(self, obj):
        return obj.has_2fa_enabled


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'confirmed_at', 'last_used_at')
    list_filter = ('is_enabled',)
    search_fields = ('user__username', 'user__email')
    actions = [reset_two_factor]
    readonly_fields = ('encrypted_secret', 'confirmed_at', 'created_at', 'updated_at', 'last_used_at')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'used', 'is_valid', 'created_at', 'expires_at')
    list_filter = ('used',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'used_at', 'ip_address')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'used', 'is_valid', 'created_at', 'expires_at')
    list_filter = ('used',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'used_at', 'ip_address')


@admin.register(BackupCode)
class BackupCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'used', 'used_at', 'created_at')
    list_filter = ('used',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('code_hash', 'created_at', 'used_at')


@admin.register(AuthenticationLog)
class AuthenticationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'user', 'username_attempted',
                    'success', 'auth_method', 'ip_address', 'browser', 'os')
    list_filter = ('event_type', 'success', 'created_at')
    search_fields = ('user__username', 'user__email', 'username_attempted', 'ip_address')
    readonly_fields = [f.name for f in AuthenticationLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'username_attempted', 'user', 'ip_address', 'reason')
    list_filter = ('reason', 'created_at')
    search_fields = ('username_attempted', 'ip_address', 'user__username')
    readonly_fields = [f.name for f in FailedLoginAttempt._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(KnownDevice)
class KnownDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'ip_address', 'is_trusted', 'last_seen', 'created_at')
    list_filter = ('is_trusted',)
    search_fields = ('user__username', 'user__email', 'label', 'ip_address')
    readonly_fields = ('device_token', 'created_at', 'last_seen')


# Register the existing domain models too (they had no admin before)
admin.site.register(ChatHistory)


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'full_name', 'incident_type', 'status', 'barangay', 'assigned_officer', 'is_archived', 'created_at')
    list_filter = ('status', 'incident_type', 'barangay', 'is_archived')
    search_fields = ('report_id', 'full_name', 'email')
    readonly_fields = ('report_id', 'created_at', 'updated_at', 'archived_at')


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'is_active')
    search_fields = ('name',)


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ('name', 'municipality', 'is_active')
    list_filter = ('municipality',)
    search_fields = ('name',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'posted_by', 'is_published', 'is_archived', 'created_at')
    list_filter = ('category', 'is_published', 'is_archived')
    search_fields = ('title', 'description')
    readonly_fields = ('archived_at',)


@admin.register(CaseTimeline)
class CaseTimelineAdmin(admin.ModelAdmin):
    list_display = ('incident', 'event_type', 'title', 'actor', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('incident__report_id', 'title', 'description')
    readonly_fields = ('created_at',)


@admin.register(CaseAssignment)
class CaseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('incident', 'officer', 'assigned_by', 'is_active', 'assigned_at')
    list_filter = ('is_active',)
    search_fields = ('incident__report_id', 'officer__username')
    readonly_fields = ('assigned_at', 'unassigned_at')


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('incident', 'category', 'original_filename', 'uploaded_by', 'file_size', 'created_at')
    list_filter = ('category',)
    search_fields = ('incident__report_id', 'original_filename', 'description')
    readonly_fields = ('file_size', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'user', 'object_type', 'object_id', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('details', 'object_id', 'user__username')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('rating', 'category', 'status', 'user', 'name', 'created_at')
    list_filter = ('status', 'rating', 'category')
    search_fields = ('message', 'name', 'email', 'user__username')
    readonly_fields = ('responded_at', 'created_at')


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'sort_order', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer')


@admin.register(AwarenessArticle)
class AwarenessArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'posted_by', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ('filename', 'backup_type', 'file_size', 'created_by', 'created_at')
    list_filter = ('backup_type',)
    search_fields = ('filename', 'notes')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')

admin.site.site_header = 'BabaengBulacan Administration'
admin.site.site_title = 'BabaengBulacan Admin'
admin.site.index_title = 'Administration'


# ---------------------------------------------------------------------------
# Authentication Security Management dashboard
# ---------------------------------------------------------------------------
@staff_member_required
def security_dashboard(request):
    """Consolidated security overview for administrators."""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    total_users = User.objects.count()
    verified_users = UserProfile.objects.filter(email_verified=True).count()
    twofa_users = TwoFactorAuth.objects.filter(is_enabled=True).count()
    locked_profiles = UserProfile.objects.filter(lockout_until__gt=now)

    # Suspicious activity: IPs with many failed attempts in the last 24h
    suspicious_ips = (
        FailedLoginAttempt.objects
        .filter(created_at__gte=last_24h)
        .values('ip_address')
        .annotate(attempts=Count('id'))
        .filter(attempts__gte=5)
        .order_by('-attempts')[:10]
    )

    context = {
        **admin.site.each_context(request),
        'title': 'Authentication Security Management',
        'total_users': total_users,
        'verified_users': verified_users,
        'unverified_users': total_users - verified_users,
        'verified_pct': round((verified_users / total_users) * 100) if total_users else 0,
        'twofa_users': twofa_users,
        'twofa_pct': round((twofa_users / total_users) * 100) if total_users else 0,
        'locked_count': locked_profiles.count(),
        'locked_profiles': locked_profiles.select_related('user')[:25],
        'failed_24h': FailedLoginAttempt.objects.filter(created_at__gte=last_24h).count(),
        'logins_24h': AuthenticationLog.objects.filter(event_type='login_success', created_at__gte=last_24h).count(),
        'new_devices_7d': AuthenticationLog.objects.filter(event_type='new_device', created_at__gte=last_7d).count(),
        'recent_logs': AuthenticationLog.objects.select_related('user')[:30],
        'recent_failures': FailedLoginAttempt.objects.select_related('user')[:25],
        'suspicious_ips': suspicious_ips,
    }
    return render(request, 'admin/security_dashboard.html', context)
