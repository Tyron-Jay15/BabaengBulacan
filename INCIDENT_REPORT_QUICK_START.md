# Incident Report Feature - Quick Start Guide

## 🎯 Feature Overview

A complete Django incident reporting system that allows users to report incidents of violence, harassment, abuse, or discrimination. This feature demonstrates essential Django concepts in a production-ready manner.

## 🚀 Getting Started

### 1. Access the Feature
- **URL**: `http://localhost:8000/reports/incident/`
- **Navbar**: Click "Services" → "Report Incident"
- **Method**: GET (view form) / POST (submit report)

### 2. Form Fields

#### Personal Information Section
- **Full Name** * (required)
  - Min 2 chars, Max 200 chars
  - Must contain at least one letter
  
- **Email Address** * (required)
  - Valid email format
  - Example: `user@example.com`
  
- **Contact Number** * (required)
  - Min 7 digits, Max 20 chars
  - Format: `09123456789` or `(123) 456-7890`

#### Incident Details Section
- **Incident Type** * (required)
  - Violence: Physical harm or threat
  - Harassment: Unwanted behavior or contact
  - Abuse: Emotional or verbal mistreatment
  - Discrimination: Unfair treatment based on gender
  - Other: Any other incident type

- **Incident Description** * (required)
  - Min 10 chars, Max 5000 chars
  - Provide detailed information
  - Include who, what, when, where, why details

- **Incident Location** * (required)
  - Min 3 chars, Max 300 chars
  - Specific location where incident occurred
  - Example: `Baliwag Public Market`, `SM Bulacan Main Street`

- **Date & Time of Incident** * (required)
  - Cannot be future date
  - Cannot be older than 5 years
  - Use the datetime picker widget

#### Evidence Section (Optional)
- **Evidence Upload** (optional)
  - Supported: PDF, DOC, DOCX, JPG, PNG, MP4, MOV
  - Max size: 50MB
  - Upload photos, videos, documents, etc.

## 📝 How to Submit a Report

1. **Navigate to Form**
   - Click on "Services" → "Report Incident" in navbar

2. **Fill Personal Information**
   - Enter your full name
   - Enter your email address
   - Enter your contact number

3. **Provide Incident Details**
   - Select the type of incident
   - Write detailed description
   - Enter location
   - Set date and time

4. **Upload Evidence (Optional)**
   - Click on the upload area
   - Select file (if needed)
   - File name will be displayed

5. **Review & Submit**
   - Review all information
   - Read privacy notice
   - Click "Submit Report"

6. **Receive Confirmation**
   - Get report ID for tracking
   - Message confirms successful submission
   - Redirected to success page

## 🔒 Security & Privacy

### Security Features
- ✅ CSRF Protection (automatic Django middleware)
- ✅ Input Validation (server & client-side)
- ✅ File Type & Size Restrictions
- ✅ Email Validation
- ✅ Date Range Validation
- ✅ SQL Injection Prevention (Django ORM)

### Privacy Protection
- 📱 Optional user association (not required to report)
- 🔐 Confidential data handling
- 📋 Privacy notice on form
- 🛡️ Data encryption ready (add in production)

## 🧪 Testing the Feature

### Manual Testing
1. **Test Valid Submission**
   ```
   - Fill all required fields with valid data
   - Submit the form
   - Verify success message and report ID
   ```

2. **Test Validation**
   ```
   - Submit with empty fields → See validation errors
   - Submit with invalid email → See error message
   - Submit with short description → See min length error
   - Submit with future date → See error message
   ```

3. **Test File Upload**
   ```
   - Upload valid file (PDF, JPG) → Success
   - Upload invalid file type → Error message
   - Upload large file (>50MB) → Error message
   ```

### Automated Testing
Run the test script:
```bash
python test_incident_report.py
```

This runs:
- Form validation tests (5 scenarios)
- View GET/POST tests
- CSRF token verification
- Database persistence tests

## 📊 Django Concepts Demonstrated

### 1. **Django Forms**
```python
from django import forms
from .models import IncidentReport

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = [...]  # Form fields
```

### 2. **Form Validation**
```python
def clean_email(self):
    email = self.cleaned_data.get('email')
    if not email:
        raise forms.ValidationError('Email is required')
    return email
```

### 3. **Class-Based View**
```python
class IncidentReportView(View):
    def get(self, request):
        # Display form
        form = IncidentReportForm()
        return render(request, 'incident_report.html', {'form': form})
    
    def post(self, request):
        # Handle submission
        form = IncidentReportForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save()
            return redirect('report_success')
```

### 4. **CSRF Protection**
```html
<!-- In template -->
{% csrf_token %}

<!-- In view -->
@method_decorator(csrf_protect, name='dispatch')
class IncidentReportView(View):
    ...
```

### 5. **File Uploads**
```python
evidence_file = forms.FileField(
    required=False,
    validators=[FileExtensionValidator(...)]
)
```

### 6. **User-Friendly UI**
- Responsive Bootstrap design
- Color-coded sections
- Clear error messages
- Help text and guidance
- Mobile-friendly layout

## 📁 File Structure

```
ProjDjango/
├── projdjango/
│   ├── forms.py                          # NEW - IncidentReportForm
│   ├── models.py                         # UPDATED - IncidentReport model
│   ├── views.py                          # UPDATED - IncidentReportView
│   ├── urls.py                           # UPDATED - incident_report route
│   ├── settings.py                       # UPDATED - media config
│   ├── migrations/
│   │   └── 0006_incidentreport.py        # NEW - Migration
│   └── templates/
│       ├── reports/
│       │   └── incident_report.html      # NEW - Form template
│       └── components/
│           └── navbar.html               # UPDATED - Navigation link
├── test_incident_report.py               # NEW - Test script
└── INCIDENT_REPORT_IMPLEMENTATION.md     # NEW - Documentation
```

## 🔍 Admin Dashboard

### Access Reports
1. Navigate to `/admin/`
2. Login with admin credentials
3. Find "Incident Reports" section
4. View, filter, and manage reports

### Useful Queries
```python
# All reports
IncidentReport.objects.all()

# By type
IncidentReport.objects.filter(incident_type='violence')

# By status
IncidentReport.objects.filter(status='submitted')

# Recent reports
IncidentReport.objects.order_by('-created_at')[:10]

# By user
user.incident_reports.all()
```

## 📱 Responsive Design

- **Desktop**: Multi-column layout with sidebar
- **Tablet**: Adjusted spacing and font sizes
- **Mobile**: Single column, touch-friendly buttons
- **File Upload**: Drag-and-drop ready (can be added)

## 🚨 Error Handling

### Common Validation Errors
```
❌ Full name must be at least 2 characters long
❌ Please provide a valid email address
❌ Contact number must be at least 7 digits
❌ Incident description must be at least 10 characters
❌ Incident date cannot be in the future
❌ File size cannot exceed 50MB
```

### Success Messages
```
✅ Thank you for reporting this incident. 
   Your report ID is: [UUID]. We will review your report shortly.
```

## 🔧 Customization

### Change File Upload Limits
In `settings.py`:
```python
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
```

### Change Incident Types
In `models.py`:
```python
INCIDENT_TYPE_CHOICES = [
    ('violence', 'Violence'),
    # Add more types
]
```

### Customize Email Notifications
In `views.py` post() method:
```python
send_email(incident)  # Add email functionality
```

## 📞 Support & Emergency

- **Emergency**: Call 911 or local emergency number
- **Police**: File a report with local authorities
- **Hotline**: [Add local hotline info]
- **Resources**: Visit Resources page for help

## 📋 Checklist for Implementation

- ✅ Model created and migrated
- ✅ Form with validation implemented
- ✅ View with GET/POST handling
- ✅ Template with responsive design
- ✅ CSRF protection enabled
- ✅ URL route configured
- ✅ Media files configured
- ✅ Navigation link added
- ✅ Tests created
- ✅ Documentation provided

## 🎓 Learning Resources

- [Django Forms Documentation](https://docs.djangoproject.com/en/stable/topics/forms/)
- [Form Validation](https://docs.djangoproject.com/en/stable/ref/forms/validation/)
- [File Uploads](https://docs.djangoproject.com/en/stable/topics/http/file-uploads/)
- [CSRF Protection](https://docs.djangoproject.com/en/stable/ref/csrf/)
- [Class-Based Views](https://docs.djangoproject.com/en/stable/topics/class-based-views/)

## 💡 Next Steps

1. Test the form submission
2. Review database records in admin
3. Customize styling to match your brand
4. Add email notifications
5. Implement case tracking system
6. Add analytics dashboard
7. Deploy to production

---

**Created**: May 2026  
**Feature Status**: ✅ Complete & Production-Ready  
**Django Version**: 6.0+  
**Database**: SQLite (ready for PostgreSQL)
