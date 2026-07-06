# Django Concepts - Code Examples & Explanations

## 1. Django Forms

### What is a Django Form?
A form is a collection of fields that tells Django how to display an HTML form and validate its data.

### Example: IncidentReportForm

```python
from django import forms
from .models import IncidentReport

class IncidentReportForm(forms.ModelForm):
    """
    ModelForm automatically creates form fields from model fields.
    Advantages:
    - DRY (Don't Repeat Yourself)
    - Automatic field type mapping
    - Validation based on model field definitions
    """
    
    # Customize specific fields
    incident_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        })
    )
    
    class Meta:
        model = IncidentReport
        fields = ['full_name', 'email', 'contact_number', ...]
```

### Key Concepts:

**ModelForm**: Generates form from model
- Automatically creates appropriate field types
- Links to database model for saving
- Reduces code duplication

**Widgets**: HTML rendering
```python
forms.TextInput(attrs={'class': 'form-control'})  # Bootstrap class
forms.DateTimeInput(attrs={'type': 'datetime-local'})  # HTML5 date picker
forms.Select()  # Dropdown for choices
forms.Textarea()  # Multi-line text
forms.FileInput()  # File upload
```

## 2. Form Validation

### Field-Level Validation
Clean individual fields before submission.

```python
def clean_full_name(self):
    """
    Called automatically when form is validated.
    Must return the cleaned data.
    """
    full_name = self.cleaned_data.get('full_name', '').strip()
    
    # Validation rules
    if not full_name:
        raise forms.ValidationError('Full name is required.')
    
    if len(full_name) < 2:
        raise forms.ValidationError('Full name must be at least 2 characters.')
    
    if not any(char.isalpha() for char in full_name):
        raise forms.ValidationError('Full name must contain at least one letter.')
    
    return full_name  # Always return cleaned data
```

### Form-Level Validation
Validate relationships between multiple fields.

```python
def clean(self):
    """
    Called after all individual field cleaning.
    Validate relationships between fields.
    """
    cleaned_data = super().clean()
    
    # Example: Cross-field validation
    incident_date = cleaned_data.get('incident_date')
    incident_type = cleaned_data.get('incident_type')
    
    if incident_type == 'violence' and not incident_date:
        raise forms.ValidationError(
            "Violence incidents must have a date."
        )
    
    return cleaned_data
```

### Custom Validators

```python
from django.core.validators import FileExtensionValidator

evidence_file = forms.FileField(
    validators=[
        FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'png'],
            message='Only PDF and image files allowed.'
        )
    ]
)
```

## 3. POST Request Handling

### What is a POST Request?
Method for submitting form data to server (secure, data in body).

### Class-Based View Example

```python
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

class IncidentReportView(View):
    """
    Handles both GET (display form) and POST (process submission) requests.
    """
    
    def get(self, request):
        """
        GET request: Display empty form
        """
        form = IncidentReportForm()
        context = {'form': form}
        return render(request, 'incident_report.html', context)
    
    def post(self, request):
        """
        POST request: Process form submission
        """
        # Bind form with data (request.POST) and files (request.FILES)
        form = IncidentReportForm(request.POST, request.FILES)
        
        # Validate form (calls all clean methods)
        if form.is_valid():
            # Form data is valid
            incident = form.save(commit=False)  # Create object but don't save yet
            
            # Add extra data if needed
            if request.user.is_authenticated:
                incident.user = request.user
            
            incident.save()  # Save to database
            
            # Add success message
            messages.success(request, f'Report submitted! ID: {incident.report_id}')
            
            # Redirect to prevent form resubmission
            return redirect('report_success')
        
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            
            # Re-render form with errors
            return render(request, 'incident_report.html', {'form': form})
```

### Request Object Properties

```python
request.POST          # Form data (dictionary-like)
request.FILES         # Uploaded files
request.user          # Authenticated user (or AnonymousUser)
request.method        # 'GET', 'POST', 'PUT', etc.
request.session       # Session data
request.META          # HTTP headers and environment
request.GET           # URL query parameters
```

### Form Binding

```python
# Unbound form (empty)
form = IncidentReportForm()

# Bound form (with data)
form = IncidentReportForm(request.POST)

# Bound form (with data and files)
form = IncidentReportForm(request.POST, request.FILES)

# Pre-filled form (for editing)
form = IncidentReportForm(request.POST, instance=incident)
```

## 4. CSRF Protection

### What is CSRF?
Cross-Site Request Forgery: Attack where attacker tricks user into performing action.

### Django's CSRF Protection

**Automatic Protection**:
```python
# In middleware (already configured)
'django.middleware.csrf.CsrfViewMiddleware'
```

**In Template**:
```html
<form method="POST">
    {% csrf_token %}  <!-- Required for all POST forms -->
    <!-- form fields -->
    <button type="submit">Submit</button>
</form>
```

**Django checks**:
- Token in form matches session token
- Rejects POST requests without valid token
- Prevents cross-site attacks

**In View** (if needed):
```python
from django.views.decorators.csrf import csrf_protect

@csrf_protect  # For function-based views
def my_view(request):
    pass

# Or for class-based views
from django.utils.decorators import method_decorator

@method_decorator(csrf_protect, name='dispatch')
class MyView(View):
    pass
```

## 5. User-Friendly UI Design

### HTML Template Structure

```html
<!-- Form wrapped in container -->
<div class="incident-report-container">
    
    <!-- Header with instructions -->
    <div class="report-header">
        <h1>Report an Incident</h1>
        <p>Help us protect women...</p>
    </div>
    
    <!-- Form with CSRF token -->
    <form method="POST" enctype="multipart/form-data">
        {% csrf_token %}
        
        <!-- Section for organization -->
        <div class="form-section">
            <h2>Personal Information</h2>
            
            <!-- Form group with label, input, errors -->
            <div class="form-group">
                <label for="full_name">Full Name *</label>
                <input type="text" class="form-control" name="full_name">
                {% if form.full_name.errors %}
                    <span class="error">{{ form.full_name.errors.0 }}</span>
                {% endif %}
            </div>
        </div>
        
        <!-- Submit button -->
        <button type="submit" class="btn btn-primary">Submit Report</button>
    </form>
</div>
```

### CSS for User Experience

```css
/* Focus state for accessibility */
.form-control:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

/* Error styling */
.error {
    color: #e74c3c;
    font-size: 0.85em;
    margin-top: 5px;
}

/* Help text */
.help-text {
    color: #7f8c8d;
    font-size: 0.9em;
    font-style: italic;
}

/* Responsive layout */
@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;  /* Stack on mobile */
    }
}
```

### JavaScript Enhancement

```javascript
// Display filename when selected
document.querySelector('input[type="file"]').addEventListener('change', function(e) {
    const fileName = this.files[0].name;
    document.getElementById('file-name').textContent = `Selected: ${fileName}`;
});
```

## 6. Complete Form Submission Flow

### Step-by-Step Process

```
1. USER REQUESTS FORM (GET)
   └─> Browser sends: GET /reports/incident/
   └─> View.get() → render form template
   └─> Template renders form with {% csrf_token %}
   └─> Browser displays empty form

2. USER FILLS FORM
   └─> User enters data in form fields
   └─> User selects incident type
   └─> User optionally uploads file

3. USER SUBMITS FORM (POST)
   └─> Browser sends: POST /reports/incident/
   └─> Data includes: form fields + csrf token + file
   └─> Request arrives at View.post()

4. VIEW PROCESSES SUBMISSION
   └─> Form = IncidentReportForm(request.POST, request.FILES)
   └─> Django calls form.is_valid()
     └─> For each field: clean_fieldname() called
     └─> Then: clean() called (cross-field validation)
     └─> Returns: True if all valid, False if any errors

5a. IF VALID
   └─> incident = form.save()
   └─> Saves to database
   └─> messages.success() adds message
   └─> redirect() prevents resubmission
   └─> Browser redirected to success page

5b. IF INVALID
   └─> form.errors contains error messages
   └─> Form re-rendered with errors displayed
   └─> User can correct and resubmit

6. BROWSER DISPLAYS RESULT
   └─> If valid: Success page + report ID
   └─> If invalid: Form with error messages highlighted
```

## 7. Best Practices

### Form Security
```python
# ✅ Always use Django forms (not manual HTML parsing)
form = IncidentReportForm(request.POST)

# ✅ Always validate on server (don't trust client-side only)
if form.is_valid():
    # Process data

# ✅ Use CSRF token in all POST forms
{% csrf_token %}

# ✅ Validate file uploads
if evidence_file.size > MAX_SIZE:
    raise ValidationError("File too large")
```

### User Experience
```python
# ✅ Provide clear error messages
raise forms.ValidationError("Email format is invalid")

# ✅ Show field-specific errors
{% if form.email.errors %}
    <span>{{ form.email.errors.0 }}</span>
{% endif %}

# ✅ Use help text
help_text="Format: 09123456789"

# ✅ Show successful submission message
messages.success(request, "Report submitted successfully!")

# ✅ Redirect after POST (prevent duplicate submission)
return redirect('success_page')
```

### Code Organization
```python
# ✅ Use ModelForm to reduce code
class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = [...]

# ✅ Separate concerns
# - models.py: data structure
# - forms.py: form definition & validation
# - views.py: business logic
# - templates/: presentation

# ✅ Use descriptive names
def clean_contact_number(self):  # Clear what it validates
    pass
```

## 8. Testing Examples

### Test Form Validation

```python
def test_valid_form():
    form_data = {
        'full_name': 'Maria Santos',
        'email': 'maria@example.com',
        'contact_number': '09123456789',
        'incident_type': 'harassment',
        'incident_description': 'I was harassed at work.',
        'incident_location': 'Office Building',
        'incident_date': '2024-05-15T14:30',
    }
    form = IncidentReportForm(data=form_data)
    assert form.is_valid()  # Should be valid

def test_invalid_email():
    form_data = {
        'email': 'not-an-email',  # Invalid email
        ...
    }
    form = IncidentReportForm(data=form_data)
    assert not form.is_valid()  # Should be invalid
    assert 'email' in form.errors  # Should have email error
```

### Test View

```python
def test_post_creates_incident():
    client = Client()
    form_data = {...}  # Valid form data
    
    response = client.post('/reports/incident/', form_data)
    
    assert response.status_code == 302  # Redirect
    assert IncidentReport.objects.count() == 1  # Created
```

---

## Summary

| Concept | Purpose | Example |
|---------|---------|---------|
| **Django Forms** | Define form structure & rendering | `IncidentReportForm(forms.ModelForm)` |
| **Validation** | Ensure data quality | `clean_email()`, `clean()` |
| **POST Handling** | Process form submission | `View.post(request)` |
| **CSRF Protection** | Prevent cross-site attacks | `{% csrf_token %}` |
| **UI Design** | User-friendly interface | Responsive CSS, error messages |

These concepts work together to create a secure, user-friendly form that handles incident reporting effectively!
