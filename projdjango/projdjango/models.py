from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta
import base64
import pickle
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    face_encoding = models.BinaryField(null=True, blank=True)  # Store pickled face encoding
    face_photo = models.ImageField(
        upload_to='face_photos/',
        null=True,
        blank=True,
        help_text='Photo captured at registration (for admin review).',
    )
    
    # Time-based security fields
    login_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    session_start_time = models.DateTimeField(null=True, blank=True)
    
    # Device name for authentication
    device_name = models.CharField(max_length=100, null=True, blank=True)

    # Email verification status
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_face_encoding(self):
        if self.face_encoding:
            try:
                return pickle.loads(self.face_encoding)
            except Exception:
                return None
        return None

    def set_face_encoding(self, encoding):
        self.face_encoding = pickle.dumps(encoding)
        self.save()

    def save_face_photo_from_base64(self, base64_string):
        """Save the registration selfie so admins can view it in the backend."""
        if not base64_string:
            return
        data = base64_string
        if ',' in data:
            data = data.split(',', 1)[1]
        try:
            raw = base64.b64decode(data)
        except (ValueError, TypeError):
            return
        filename = f'user_{self.user_id or "new"}_{uuid.uuid4().hex[:8]}.jpg'
        if self.face_photo:
            self.face_photo.delete(save=False)
        self.face_photo.save(filename, ContentFile(raw), save=False)

    @property
    def has_registered_face(self):
        return bool(self.face_encoding)

    @property
    def has_face_photo(self):
        return bool(self.face_photo)

    def is_locked_out(self):
        """Check if user is currently locked out"""
        if self.lockout_until and timezone.now() < self.lockout_until:
            return True
        return False

    def record_failed_attempt(self):
        """Record a failed login attempt. Returns True if the account just locked."""
        from django.conf import settings
        was_locked = self.is_locked_out()
        self.login_attempts += 1
        self.last_login_attempt = timezone.now()

        just_locked = False
        if self.login_attempts >= getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5):
            self.lockout_until = timezone.now() + timedelta(seconds=getattr(settings, 'LOCKOUT_DURATION', 900))
            just_locked = not was_locked

        self.save()
        return just_locked

    def record_successful_login(self):
        """Reset login attempts on successful login"""
        self.login_attempts = 0
        self.lockout_until = None
        self.last_login_attempt = timezone.now()
        self.session_start_time = timezone.now()
        self.save()

    def get_remaining_lockout_time(self):
        """Get remaining lockout time in seconds"""
        if self.lockout_until and timezone.now() < self.lockout_until:
            return int((self.lockout_until - timezone.now()).total_seconds())
        return 0

    def is_session_expired(self):
        """Check if user session has expired"""
        from django.conf import settings
        if self.session_start_time:
            session_timeout = getattr(settings, 'SESSION_TIMEOUT', 3600)
            return (timezone.now() - self.session_start_time).total_seconds() > session_timeout
        return False

    def get_session_remaining_time(self):
        """Get remaining session time in seconds"""
        from django.conf import settings
        if self.session_start_time:
            session_timeout = getattr(settings, 'SESSION_TIMEOUT', 3600)
            elapsed = (timezone.now() - self.session_start_time).total_seconds()
            remaining = session_timeout - elapsed
            return max(0, int(remaining))
        return 0

    def mark_email_verified(self):
        """Mark this user's email as verified."""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified', 'email_verified_at'])

    @property
    def has_2fa_enabled(self):
        """Whether the user has confirmed/active TOTP two-factor auth."""
        try:
            twofa = getattr(self.user, 'two_factor', None)
            return bool(twofa and twofa.is_enabled)
        except Exception:
            return False


class ChatHistory(models.Model):
    """Model to store chat messages between users and the chatbot"""
    
    # Anonymous session ID for tracking conversations without requiring login
    session_id = models.CharField(max_length=36, default=uuid.uuid4)
    
    # User (optional - for logged-in users)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chats')
    
    # User message
    user_message = models.TextField()
    
    # Chatbot response
    bot_response = models.TextField()
    
    # Confidence score of the response (0-1)
    confidence = models.FloatField(default=0.0)
    
    # Which FAQ was matched (if any)
    faq_id = models.IntegerField(null=True, blank=True)
    
    # Intent detected by chatbot
    intent = models.CharField(
        max_length=50,
        choices=[
            ('emergency', 'Emergency'),
            ('location', 'Location Query'),
            ('information', 'Information Request'),
            ('help', 'Help Request'),
            ('general', 'General Question'),
            ('unclear', 'Unclear'),
        ],
        default='general'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Chat {self.session_id[:8]} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class IncidentReport(models.Model):
    """Model to store incident reports for violence, harassment, abuse, or discrimination"""
    
    INCIDENT_TYPE_CHOICES = [
        ('violence', 'Violence'),
        ('harassment', 'Harassment'),
        ('abuse', 'Abuse'),
        ('discrimination', 'Discrimination'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Basic information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    
    # Incident details
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPE_CHOICES)
    incident_description = models.TextField()
    incident_location = models.CharField(max_length=300)
    incident_date = models.DateTimeField()

    # Geographic assignment (Barangay / Municipality management module)
    barangay = models.ForeignKey(
        'Barangay', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incident_reports',
    )

    # Optional evidence
    evidence_file = models.FileField(upload_to='incident_evidence/', null=True, blank=True)

    # System fields
    report_id = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    assigned_officer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_incidents',
        limit_choices_to={'is_staff': True},
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incident_reports')
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Report {self.report_id[:8]} - {self.incident_type.title()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def municipality(self):
        """Return the municipality via the barangay relationship."""
        return self.barangay.municipality if self.barangay_id else None

    def get_incident_type_display_label(self):
        return dict(self.INCIDENT_TYPE_CHOICES).get(self.incident_type, self.incident_type)

    def get_status_display_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


# ===========================================================================
# Geographic & community management models
# ===========================================================================

class Municipality(models.Model):
    """Municipality within Bulacan province."""
    name = models.CharField(max_length=120, unique=True)
    province = models.CharField(max_length=120, default='Bulacan')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Municipalities'

    def __str__(self):
        return self.name


class Barangay(models.Model):
    """Barangay under a municipality."""
    name = models.CharField(max_length=120)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='barangays')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Barangays'
        unique_together = ('name', 'municipality')

    def __str__(self):
        return f"{self.name}, {self.municipality.name}"


class Announcement(models.Model):
    """Official announcements posted by administrators."""
    CATEGORY_CHOICES = [
        ('awareness', 'Awareness'),
        ('event', 'Event'),
        ('alert', 'Alert'),
        ('program', 'Program'),
        ('general', 'General'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='general')
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='announcements',
    )
    is_published = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['is_published', '-created_at']),
        ]

    def __str__(self):
        return self.title


class Notification(models.Model):
    """User notifications for report updates, announcements, and security alerts."""
    NOTIFICATION_TYPES = [
        ('report_update', 'Report Status Update'),
        ('announcement', 'Announcement'),
        ('security', 'Security Alert'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=32, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    related_report = models.ForeignKey(
        IncidentReport, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.username}"


# ===========================================================================
# Case management models (timeline, assignment, evidence)
# ===========================================================================

class CaseTimeline(models.Model):
    """Chronological activity log for a single incident report."""

    EVENT_CHOICES = [
        ('submitted', 'Report Submitted'),
        ('assigned', 'Assigned to Officer'),
        ('reassigned', 'Reassigned'),
        ('under_review', 'Under Review'),
        ('investigation', 'Investigation Started'),
        ('evidence_uploaded', 'Evidence Uploaded'),
        ('status_updated', 'Status Updated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('note', 'Admin Note'),
    ]

    incident = models.ForeignKey(
        IncidentReport, on_delete=models.CASCADE, related_name='timeline_events',
    )
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_actions',
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['incident', 'created_at']),
        ]

    def __str__(self):
        return f"{self.incident.report_id[:8]} — {self.title}"


class CaseAssignment(models.Model):
    """Assignment history — supports reassign and officer workload tracking."""

    incident = models.ForeignKey(
        IncidentReport, on_delete=models.CASCADE, related_name='assignment_history',
    )
    officer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='case_assignments', limit_choices_to={'is_staff': True},
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments_made',
    )
    notes = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['officer', 'is_active']),
            models.Index(fields=['incident', '-assigned_at']),
        ]

    def __str__(self):
        officer = self.officer.username if self.officer else 'unassigned'
        return f"Assignment {self.incident.report_id[:8]} → {officer}"


class Evidence(models.Model):
    """Multi-file evidence attached to an incident (admin or reporter uploads)."""

    CATEGORY_CHOICES = [
        ('photo', 'Photograph'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.mp4', '.mp3'}

    incident = models.ForeignKey(
        IncidentReport, on_delete=models.CASCADE, related_name='evidence_items',
    )
    file = models.FileField(upload_to='case_evidence/%Y/%m/')
    original_filename = models.CharField(max_length=255, blank=True, default='')
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=300, blank=True, default='')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_evidence',
    )
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Evidence'

    def __str__(self):
        return f"Evidence for {self.incident.report_id[:8]} ({self.category})"

    @property
    def is_image(self):
        name = (self.file.name or '').lower()
        return name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

    @property
    def is_pdf(self):
        return (self.file.name or '').lower().endswith('.pdf')


class AuditLog(models.Model):
    """System-wide audit trail for admin and case actions (beyond auth logs)."""

    ACTION_CHOICES = [
        ('report_created', 'Report Created'),
        ('report_updated', 'Report Updated'),
        ('status_changed', 'Status Changed'),
        ('case_assigned', 'Case Assigned'),
        ('case_reassigned', 'Case Reassigned'),
        ('evidence_uploaded', 'Evidence Uploaded'),
        ('announcement_created', 'Announcement Created'),
        ('announcement_updated', 'Announcement Updated'),
        ('user_updated', 'User Updated'),
        ('report_archived', 'Report Archived'),
        ('backup_created', 'Backup Created'),
        ('backup_restored', 'Backup Restored'),
        ('feedback_responded', 'Feedback Responded'),
        ('faq_updated', 'FAQ Updated'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs',
    )
    action = models.CharField(max_length=64, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=64, blank=True, default='')
    object_id = models.CharField(max_length=64, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser = models.CharField(max_length=120, blank=True, default='')
    details = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        who = self.user.username if self.user else 'system'
        return f"{self.get_action_display()} by {who}"


class Feedback(models.Model):
    """Resident feedback and usability ratings."""

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_submissions',
    )
    name = models.CharField(max_length=120, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    message = models.TextField()
    category = models.CharField(max_length=64, blank=True, default='general')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, default='')
    responded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_responses',
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback ({self.rating}/5) — {self.created_at:%Y-%m-%d}"


class FAQItem(models.Model):
    """Administrator-managed FAQ entries."""

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('reporting', 'Reporting'),
        ('security', 'Security & Privacy'),
        ('programs', 'Programs'),
        ('legal', 'Legal Rights'),
    ]

    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='general')
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'question']
        verbose_name = 'FAQ item'

    def __str__(self):
        return self.question[:60]


class AwarenessArticle(models.Model):
    """Public awareness / educational content managed by administrators."""

    CATEGORY_CHOICES = [
        ('rights', "Women's Rights"),
        ('safety', 'Safety Tips'),
        ('emergency', 'Emergency Contacts'),
        ('programs', 'Government Programs'),
        ('resources', 'Downloadable Resources'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField()
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='rights')
    attachment = models.FileField(upload_to='awareness/', null=True, blank=True)
    is_published = models.BooleanField(default=True)
    posted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='awareness_articles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class BackupHistory(models.Model):
    """Record of database backup operations."""

    BACKUP_TYPES = [
        ('manual', 'Manual Download'),
        ('scheduled', 'Scheduled'),
        ('restore', 'Restore'),
    ]

    filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField(default=0)
    backup_type = models.CharField(max_length=32, choices=BACKUP_TYPES, default='manual')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='backups_created',
    )
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Backup history'

    def __str__(self):
        return f"{self.filename} ({self.get_backup_type_display()})"


# ===========================================================================
# Authentication & Security models
# ===========================================================================

def _default_token():
    """Generate a URL-safe random token."""
    import secrets
    return secrets.token_urlsafe(48)


class TokenQuerySet(models.QuerySet):
    def valid(self):
        return self.filter(used=False, expires_at__gt=timezone.now())


class BaseToken(models.Model):
    """Abstract base for time-limited, single-use tokens."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True, default=_default_token, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    objects = TokenQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def is_valid(self):
        return (not self.used) and timezone.now() < self.expires_at

    def mark_used(self):
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'used_at'])


class EmailVerificationToken(BaseToken):
    """Token emailed to the user to confirm their email address."""

    class Meta(BaseToken.Meta):
        verbose_name = 'Email verification token'
        verbose_name_plural = 'Email verification tokens'

    def __str__(self):
        return f"EmailVerification<{self.user.username}> valid={self.is_valid()}"


class PasswordResetToken(BaseToken):
    """Token emailed to the user to reset their password."""

    class Meta(BaseToken.Meta):
        verbose_name = 'Password reset token'
        verbose_name_plural = 'Password reset tokens'

    def __str__(self):
        return f"PasswordReset<{self.user.username}> valid={self.is_valid()}"


class TwoFactorAuth(models.Model):
    """Stores a user's encrypted TOTP secret and 2FA state."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    encrypted_secret = models.TextField(blank=True, default='')  # Fernet-encrypted base32 secret
    is_enabled = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Two-factor authentication'
        verbose_name_plural = 'Two-factor authentication'

    def __str__(self):
        return f"2FA<{self.user.username}> enabled={self.is_enabled}"

    def set_secret(self, plain_secret):
        """Encrypt and store the TOTP secret."""
        from .security import encrypt_value
        self.encrypted_secret = encrypt_value(plain_secret)

    def get_secret(self):
        """Decrypt and return the TOTP secret (or None)."""
        from .security import decrypt_value
        if not self.encrypted_secret:
            return None
        return decrypt_value(self.encrypted_secret)


class BackupCode(models.Model):
    """Single-use backup recovery code for 2FA (stored hashed)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_codes')
    code_hash = models.CharField(max_length=255)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"BackupCode<{self.user.username}> used={self.used}"


class AuthenticationLog(models.Model):
    """Audit log of authentication-related events."""

    EVENT_CHOICES = [
        ('register', 'Registration'),
        ('email_verified', 'Email Verified'),
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('2fa_success', '2FA Success'),
        ('2fa_failed', '2FA Failed'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('2fa_reset', '2FA Reset (admin)'),
        ('password_reset_request', 'Password Reset Requested'),
        ('password_changed', 'Password Changed'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('account_recovered', 'Account Recovered'),
        ('new_device', 'New Device Login'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='auth_logs')
    username_attempted = models.CharField(max_length=254, blank=True, default='')
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    auth_method = models.CharField(max_length=64, blank=True, default='')
    success = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    device = models.CharField(max_length=120, blank=True, default='')
    browser = models.CharField(max_length=120, blank=True, default='')
    os = models.CharField(max_length=120, blank=True, default='')
    details = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]

    def __str__(self):
        who = self.user.username if self.user else (self.username_attempted or 'unknown')
        return f"{self.get_event_type_display()} - {who} @ {self.created_at:%Y-%m-%d %H:%M}"


class FailedLoginAttempt(models.Model):
    """Records individual failed login attempts for monitoring / rate limiting."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='failed_attempts')
    username_attempted = models.CharField(max_length=254, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    reason = models.CharField(max_length=120, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username_attempted', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]

    def __str__(self):
        return f"FailedLogin<{self.username_attempted}> @ {self.created_at:%Y-%m-%d %H:%M}"


class KnownDevice(models.Model):
    """A device/browser previously used to successfully sign in (for new-device alerts)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='known_devices')
    device_token = models.CharField(max_length=128, db_index=True)  # random token stored in a cookie
    label = models.CharField(max_length=200, blank=True, default='')
    browser = models.CharField(max_length=120, blank=True, default='')
    os = models.CharField(max_length=120, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_trusted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_seen']
        unique_together = ('user', 'device_token')

    def __str__(self):
        return f"Device<{self.user.username}> {self.label}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            email_verified=instance.is_staff or instance.is_superuser,
            email_verified_at=timezone.now() if (instance.is_staff or instance.is_superuser) else None,
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    instance.userprofile.save()