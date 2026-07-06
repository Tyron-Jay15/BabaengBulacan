# Report Incident Feature - Implementation Summary

## Overview
A complete Django feature for reporting incidents involving violence, harassment, abuse, or discrimination against women. This feature demonstrates key Django concepts including Forms, Form Validation, POST Request Handling, CSRF Protection, and User-Friendly UI Design.

## Features Implemented

### 1. **Database Model** (`models.py`)
- **IncidentReport Model**: Stores incident report data with the following fields:
  - `full_name` - Reporter's full name
  - `email` - Reporter's email address
  - `contact_number` - Reporter's contact number
  - `incident_type` - Type of incident (Violence, Harassment, Abuse, Discrimination, Other)
  - `incident_description` - Detailed description of the incident
  - `incident_location` - Where the incident occurred
  - `incident_date` - When the incident occurred
  - `evidence_file` - Optional file upload for supporting evidence
  - `report_id` - Unique identifier for each report (UUID)
  - `status` - Report status (Submitted, Under Review, Resolved, Closed)
  - `user` - Optional link to authenticated user
  - `created_at` & `updated_at` - Automatic timestamps

### 2. **Django Form** (`forms.py`)
- **IncidentReportForm**: ModelForm with comprehensive validation

#### Key Features:
- **Form Validation**: Custom validators for each field
  - Full Name: Min 2 chars, max 200 chars, must contain letters
  - Email: Standard email validation
  - Contact Number: Min 7 digits, max 20 chars
  - Description: Min 10 chars, max 5000 chars
  - Location: Min 3 chars, max 300 chars
  - Incident Date: Cannot be future date, cannot be older than 5 years
  - File Upload: Max 50MB, allowed formats: PDF, DOC, DOCX, JPG, PNG, MP4, MOV

- **File Validation**: 
  - File extension validation
  - File size validation
  - User-friendly error messages

- **User-Friendly Widgets**:
  - Bootstrap CSS classes integrated
  - Placeholder text for guidance
  - Help text for each field
  - DateTime picker for date/time selection
  - Custom file upload UI

### 3. **View (Class-Based)** (`views.py`)
- **IncidentReportView**: Handles both GET and POST requests

#### GET Request (Display Form):
- Renders empty incident report form
- Sets up context with page title
- Uses CSRF protection via decorator

#### POST Request (Handle Submission):
- Validates form data
- Handles file uploads
- Associates report with logged-in user (if authenticated)
- Saves to database
- Displays success/error messages
- Redirects to success page on successful submission
- Returns to form with errors on validation failure

### 4. **URL Configuration** (`urls.py`)
- Route: `/reports/incident/` (GET & POST)
- Name: `incident_report`
- Class-based view: `IncidentReportView.as_view()`

### 5. **Settings Configuration** (`settings.py`)
Added media file configuration:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MAX_UPLOAD_SIZE = 52428800  # 50MB
```

### 6. **HTML Template** (`templates/reports/incident_report.html`)

#### Features:
- **Responsive Design**: Mobile-friendly layout using CSS Grid
- **User-Friendly UI**:
  - Clear section headers with icons
  - Color-coded form sections
  - Organized form layout
  - Visual indicators for required fields
  
- **Accessibility**:
  - Proper label associations
  - ARIA-friendly structure
  - Clear error messages
  - Help text for guidance

- **Security**:
  - CSRF token embedded
  - File type and size restrictions displayed
  - Privacy notice explaining data handling
  - Emergency contact information

- **Styling**:
  - Modern gradient design
  - Smooth transitions and hover effects
  - Color-coded incident types
  - Responsive file upload widget
  - Enhanced form controls

- **JavaScript Enhancement**:
  - Dynamic file name display
  - File size display

## Django Concepts Demonstrated

### 1. **Django Forms**
- ModelForm usage
- Field customization
- Widget configuration
- Form rendering in templates
- CSRF token integration

### 2. **Form Validation**
- Field-level validation (`clean_<fieldname>()`)
- Form-level validation (`clean()`)
- Custom validators
- Error message customization

### 3. **POST Request Handling**
- Request method checking
- Form data binding
- File upload handling
- Database model saving

### 4. **CSRF Protection**
- Automatic CSRF middleware integration
- `{% csrf_token %}` in template
- `@method_decorator(csrf_protect)` on view
- Secure form submission

### 5. **User-Friendly UI Design**
- Bootstrap CSS integration
- Responsive layout
- Color-coded sections
- Clear error messages
- Help text and guidance
- Progressive enhancement

## How to Use

### For Users:
1. Navigate to `/reports/incident/`
2. Fill in personal information
3. Select incident type and provide details
4. Optionally upload evidence
5. Click "Submit Report"
6. Receive confirmation with report ID

### For Developers:
1. Access stored reports via Django admin
2. Query: `IncidentReport.objects.all()`
3. Filter by status, type, or date
4. Access uploaded files via `incident.evidence_file.url`

## Database Migration
- Migration file: `0006_incidentreport.py`
- Run: `python manage.py migrate`

## File Structure
```
projdjango/
├── forms.py                                    (NEW - Form definition)
├── models.py                                   (UPDATED - IncidentReport model)
├── views.py                                    (UPDATED - IncidentReportView)
├── urls.py                                     (UPDATED - incident_report route)
├── settings.py                                 (UPDATED - media files config)
├── migrations/
│   └── 0006_incidentreport.py                 (NEW - Migration)
└── templates/reports/
    └── incident_report.html                    (NEW - Form template)
```

## Security Features
1. **CSRF Protection**: Built-in Django CSRF middleware
2. **File Validation**: Type and size restrictions
3. **Input Validation**: Comprehensive field validation
4. **Data Privacy**: Optional user association
5. **Error Handling**: Safe error messages
6. **Rate Limiting Ready**: Can be added via middleware

## Future Enhancements
- Email notifications to administrators
- Case tracking system
- PDF report generation
- Automated response emails
- Multi-language support
- SMS alerts for urgent cases
- Integration with external services
- Analytics dashboard
- Case status tracking for reporters

## Testing Checklist
- [ ] Form displays correctly (GET request)
- [ ] Form submits successfully (POST request)
- [ ] File upload works (valid file)
- [ ] File validation rejects invalid files
- [ ] Validation messages display correctly
- [ ] Success redirect works
- [ ] Database saves records
- [ ] CSRF token present
- [ ] Mobile responsive layout
- [ ] Error handling works
