"""
DRF Serializers for BabaengBulacan.

Serializers translate Django model instances into JSON (and validate incoming
JSON for POST/PUT/PATCH). Each serializer maps to an existing project model.
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from projdjango.models import (
    UserProfile, IncidentReport, Announcement, Municipality, Barangay,
    Notification, AuthenticationLog,
)


# ---------------------------------------------------------------------------
# Users API  →  /api/users/
# ---------------------------------------------------------------------------
class UserAPISerializer(serializers.ModelSerializer):
    """
    Exposes User + UserProfile fields required by Activity 9.

    JSON fields:
      id, full_name, email, role, verified, account_status, date_registered
    """
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    date_registered = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'role',
            'verified', 'account_status', 'date_registered',
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        name = obj.get_full_name().strip()
        return name if name else obj.username

    def get_role(self, obj):
        if obj.is_superuser:
            return 'Super Admin'
        if obj.is_staff:
            return 'Admin'
        return 'Resident'

    def get_verified(self, obj):
        try:
            return obj.userprofile.email_verified
        except UserProfile.DoesNotExist:
            return False

    def get_account_status(self, obj):
        if not obj.is_active:
            return 'Inactive'
        try:
            if obj.userprofile.is_locked_out():
                return 'Locked'
        except UserProfile.DoesNotExist:
            pass
        return 'Active'


# ---------------------------------------------------------------------------
# Incident Reports API  →  /api/incidents/
# ---------------------------------------------------------------------------
class IncidentReportAPISerializer(serializers.ModelSerializer):
    """
    JSON fields:
      id, report_id, reporter, incident_type, barangay, municipality,
      date_reported, status, assigned_officer
    """
    id = serializers.IntegerField(read_only=True)
    reporter = serializers.CharField(source='full_name', read_only=True)
    incident_type = serializers.SerializerMethodField()
    barangay = serializers.SerializerMethodField()
    municipality = serializers.SerializerMethodField()
    date_reported = serializers.DateTimeField(source='created_at', read_only=True)
    status = serializers.SerializerMethodField()
    assigned_officer = serializers.SerializerMethodField()

    class Meta:
        model = IncidentReport
        fields = [
            'id', 'report_id', 'reporter', 'incident_type',
            'barangay', 'municipality', 'date_reported',
            'status', 'assigned_officer',
        ]

    def get_incident_type(self, obj):
        return obj.get_incident_type_display_label()

    def get_barangay(self, obj):
        return obj.barangay.name if obj.barangay_id else None

    def get_municipality(self, obj):
        if obj.barangay_id:
            return obj.barangay.municipality.name
        return None

    def get_status(self, obj):
        return obj.get_status_display_label()

    def get_assigned_officer(self, obj):
        if obj.assigned_officer_id:
            officer = obj.assigned_officer
            name = officer.get_full_name().strip()
            return name if name else officer.username
        return None


class IncidentReportCreateSerializer(serializers.ModelSerializer):
    """POST payload for creating a new incident report via the API."""

    class Meta:
        model = IncidentReport
        fields = [
            'full_name', 'email', 'contact_number',
            'incident_type', 'incident_description',
            'incident_location', 'incident_date', 'barangay',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Announcements API  →  /api/announcements/
# ---------------------------------------------------------------------------
class AnnouncementAPISerializer(serializers.ModelSerializer):
    """
    JSON fields:
      id, title, description, date_posted, posted_by
    """
    date_posted = serializers.DateTimeField(source='created_at', read_only=True)
    posted_by = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'description', 'category', 'date_posted', 'posted_by']
        read_only_fields = ['id', 'date_posted', 'posted_by']

    def get_posted_by(self, obj):
        if obj.posted_by_id:
            name = obj.posted_by.get_full_name().strip()
            return name if name else obj.posted_by.username
        return 'System'


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """POST payload for staff-created announcements."""

    class Meta:
        model = Announcement
        fields = ['title', 'description', 'is_published']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['posted_by'] = request.user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Optional APIs
# ---------------------------------------------------------------------------
class MunicipalityAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ['id', 'name', 'province', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class BarangayAPISerializer(serializers.ModelSerializer):
    municipality = serializers.CharField(source='municipality.name', read_only=True)
    municipality_id = serializers.PrimaryKeyRelatedField(
        source='municipality', queryset=Municipality.objects.all(), write_only=True,
    )

    class Meta:
        model = Barangay
        fields = ['id', 'name', 'municipality', 'municipality_id', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'is_read', 'related_report', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AuthenticationLogAPISerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    event = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = AuthenticationLog
        fields = [
            'id', 'user', 'username_attempted', 'event', 'event_type',
            'auth_method', 'success', 'ip_address', 'device',
            'browser', 'os', 'details', 'created_at',
        ]
        read_only_fields = fields

    def get_user(self, obj):
        if obj.user_id:
            return obj.user.username
        return None
