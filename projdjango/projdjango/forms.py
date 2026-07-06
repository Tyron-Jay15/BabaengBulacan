"""
Forms for BabaengBulacan application
"""
from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
from .models import IncidentReport


class IncidentReportForm(forms.ModelForm):
    """
    Form for reporting incidents involving violence, harassment, abuse, or discrimination.
    
    Demonstrates Django concepts:
    - Forms API and ModelForm
    - Field validation
    - Custom clean methods
    - File field with validators
    - CSRF protection (automatic in Django)
    - User-friendly widgets and help text
    """
    
    # Custom field for better UX
    incident_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
            'required': True,
        }),
        label='Date & Time of Incident',
        help_text='When did the incident occur?',
        error_messages={
            'required': 'Please provide the date and time of the incident.',
            'invalid': 'Please enter a valid date and time format.',
        }
    )
    
    evidence_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov',
        }),
        label='Evidence Upload (Optional)',
        help_text='Supported formats: PDF, DOC, DOCX, JPG, PNG, MP4, MOV. Max size: 50MB',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'mp4', 'mov'],
                message='Only PDF, Word documents, images, and video files are allowed.'
            )
        ],
        error_messages={
            'invalid_extension': 'The file type is not supported. Please use PDF, image, or video files.',
        }
    )
    
    class Meta:
        model = IncidentReport
        fields = [
            'full_name',
            'email',
            'contact_number',
            'incident_type',
            'incident_description',
            'incident_location',
            'incident_date',
            'evidence_file',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True,
                'type': 'email',
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your contact number',
                'required': True,
                'type': 'tel',
            }),
            'incident_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'incident_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Provide detailed description of the incident',
                'rows': 6,
                'required': True,
            }),
            'incident_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where did the incident occur?',
                'required': True,
            }),
        }
        labels = {
            'full_name': 'Full Name *',
            'email': 'Email Address *',
            'contact_number': 'Contact Number *',
            'incident_type': 'Type of Incident *',
            'incident_description': 'Incident Description *',
            'incident_location': 'Incident Location *',
            'incident_date': 'Date & Time of Incident *',
            'evidence_file': 'Evidence Upload (Optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default choices label
        self.fields['incident_type'].label_from_instance = lambda obj: obj.get_display_name() if hasattr(obj, 'get_display_name') else str(obj)
    
    # Custom validation methods
    
    def clean_full_name(self):
        """Validate full name field"""
        full_name = self.cleaned_data.get('full_name', '').strip()
        
        if not full_name:
            raise forms.ValidationError('Full name is required.')
        
        if len(full_name) < 2:
            raise forms.ValidationError('Full name must be at least 2 characters long.')
        
        if len(full_name) > 200:
            raise forms.ValidationError('Full name cannot exceed 200 characters.')
        
        # Check if name contains at least one letter
        if not any(char.isalpha() for char in full_name):
            raise forms.ValidationError('Full name must contain at least one letter.')
        
        return full_name
    
    def clean_email(self):
        """Validate email field"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise forms.ValidationError('Email address is required.')
        
        return email
    
    def clean_contact_number(self):
        """Validate contact number field"""
        contact_number = self.cleaned_data.get('contact_number', '').strip()
        
        if not contact_number:
            raise forms.ValidationError('Contact number is required.')
        
        # Remove common formatting characters
        cleaned_number = ''.join(filter(str.isdigit, contact_number))
        
        if len(cleaned_number) < 7:
            raise forms.ValidationError('Please provide a valid contact number (at least 7 digits).')
        
        if len(contact_number) > 20:
            raise forms.ValidationError('Contact number is too long.')
        
        return contact_number
    
    def clean_incident_description(self):
        """Validate incident description"""
        description = self.cleaned_data.get('incident_description', '').strip()
        
        if not description:
            raise forms.ValidationError('Incident description is required.')
        
        if len(description) < 10:
            raise forms.ValidationError('Please provide a detailed description (at least 10 characters).')
        
        if len(description) > 5000:
            raise forms.ValidationError('Description cannot exceed 5000 characters.')
        
        return description
    
    def clean_incident_location(self):
        """Validate incident location"""
        location = self.cleaned_data.get('incident_location', '').strip()
        
        if not location:
            raise forms.ValidationError('Incident location is required.')
        
        if len(location) < 3:
            raise forms.ValidationError('Please provide a specific location (at least 3 characters).')
        
        if len(location) > 300:
            raise forms.ValidationError('Location cannot exceed 300 characters.')
        
        return location
    
    def clean_incident_date(self):
        """Validate incident date and time"""
        incident_date = self.cleaned_data.get('incident_date')
        
        if not incident_date:
            raise forms.ValidationError('Incident date and time are required.')
        
        # Check if date is not in the future
        if incident_date > timezone.now():
            raise forms.ValidationError('Incident date cannot be in the future.')
        
        # Check if date is not too old (e.g., more than 5 years)
        five_years_ago = timezone.now() - timedelta(days=5*365)
        if incident_date < five_years_ago:
            raise forms.ValidationError('Incident date is too old (cannot be older than 5 years).')
        
        return incident_date
    
    def clean_evidence_file(self):
        """Validate evidence file"""
        evidence_file = self.cleaned_data.get('evidence_file')
        
        if evidence_file:
            # Check file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB in bytes
            if evidence_file.size > max_size:
                raise forms.ValidationError(f'File size cannot exceed 50MB. Your file is {evidence_file.size / (1024*1024):.2f}MB.')
            
            # Additional validation for file name
            if len(evidence_file.name) > 200:
                raise forms.ValidationError('File name is too long.')
        
        return evidence_file
    
    def clean(self):
        """Overall form validation"""
        cleaned_data = super().clean()
        
        # You can add cross-field validation here if needed
        # For example, validate relationships between multiple fields
        
        return cleaned_data
