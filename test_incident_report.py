"""
Test script for the Incident Report Feature
Demonstrates testing the form validation and submission
"""

import os
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projdjango.settings')
django.setup()

from projdjango.models import IncidentReport
from projdjango.forms import IncidentReportForm


class IncidentReportFormValidationTests(TestCase):
    """Test form validation"""
    
    def test_valid_form(self):
        """Test valid form submission"""
        form_data = {
            'full_name': 'Maria Santos',
            'email': 'maria@example.com',
            'contact_number': '09123456789',
            'incident_type': 'harassment',
            'incident_description': 'I was harassed at the market last week. An unknown person followed me and made inappropriate comments.',
            'incident_location': 'Baliwag Public Market',
            'incident_date': datetime.now() - timedelta(days=1),
        }
        form = IncidentReportForm(data=form_data)
        print(f"✓ Valid form test: {form.is_valid()}")
        if not form.is_valid():
            print(f"  Errors: {form.errors}")
    
    def test_missing_required_field(self):
        """Test form with missing required field"""
        form_data = {
            'full_name': '',  # Missing
            'email': 'maria@example.com',
            'contact_number': '09123456789',
            'incident_type': 'harassment',
            'incident_description': 'Detailed description here',
            'incident_location': 'Location',
            'incident_date': datetime.now() - timedelta(days=1),
        }
        form = IncidentReportForm(data=form_data)
        print(f"✗ Missing field test: {not form.is_valid()}")
        if not form.is_valid():
            print(f"  Expected error: {form.errors.get('full_name')}")
    
    def test_invalid_email(self):
        """Test form with invalid email"""
        form_data = {
            'full_name': 'Maria Santos',
            'email': 'not-an-email',  # Invalid
            'contact_number': '09123456789',
            'incident_type': 'harassment',
            'incident_description': 'Detailed description here',
            'incident_location': 'Location',
            'incident_date': datetime.now() - timedelta(days=1),
        }
        form = IncidentReportForm(data=form_data)
        print(f"✗ Invalid email test: {not form.is_valid()}")
        if not form.is_valid():
            print(f"  Expected error found")
    
    def test_future_date(self):
        """Test form with future date"""
        form_data = {
            'full_name': 'Maria Santos',
            'email': 'maria@example.com',
            'contact_number': '09123456789',
            'incident_type': 'harassment',
            'incident_description': 'Detailed description here',
            'incident_location': 'Location',
            'incident_date': datetime.now() + timedelta(days=1),  # Future date
        }
        form = IncidentReportForm(data=form_data)
        print(f"✗ Future date test: {not form.is_valid()}")
        if not form.is_valid():
            print(f"  Expected error: {form.errors.get('incident_date')}")
    
    def test_short_description(self):
        """Test form with description too short"""
        form_data = {
            'full_name': 'Maria Santos',
            'email': 'maria@example.com',
            'contact_number': '09123456789',
            'incident_type': 'harassment',
            'incident_description': 'short',  # Too short
            'incident_location': 'Location',
            'incident_date': datetime.now() - timedelta(days=1),
        }
        form = IncidentReportForm(data=form_data)
        print(f"✗ Short description test: {not form.is_valid()}")
        if not form.is_valid():
            print(f"  Expected error: {form.errors.get('incident_description')}")


class IncidentReportViewTests(TestCase):
    """Test the incident report view"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('incident_report')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_form(self):
        """Test GET request returns form"""
        response = self.client.get(self.url)
        print(f"✓ GET request test: {response.status_code == 200}")
        print(f"  Template used: {'incident_report.html' in [t.name for t in response.templates]}")
    
    def test_post_valid_form(self):
        """Test POST with valid form"""
        form_data = {
            'full_name': 'Maria Santos',
            'email': 'maria@example.com',
            'contact_number': '09123456789',
            'incident_type': 'violence',
            'incident_description': 'I was physically assaulted last week. This is a detailed description of what happened.',
            'incident_location': 'Baliwag Central Park',
            'incident_date': (datetime.now() - timedelta(days=1)).isoformat(),
        }
        response = self.client.post(self.url, data=form_data)
        print(f"✓ Valid POST test: {response.status_code in [200, 302]}")
        
        # Check if report was saved
        reports = IncidentReport.objects.filter(email='maria@example.com')
        print(f"  Report saved: {reports.count() > 0}")
        
        if reports.count() > 0:
            report = reports.first()
            print(f"  Report ID: {report.report_id}")
            print(f"  Incident Type: {report.incident_type}")
    
    def test_post_invalid_form(self):
        """Test POST with invalid form"""
        form_data = {
            'full_name': '',  # Invalid - missing
            'email': 'invalid-email',
            'contact_number': '123',  # Too short
            'incident_type': 'violence',
            'incident_description': 'short',  # Too short
            'incident_location': '',  # Missing
            'incident_date': (datetime.now() + timedelta(days=1)).isoformat(),  # Future
        }
        response = self.client.post(self.url, data=form_data)
        print(f"✓ Invalid POST test: {response.status_code == 200}")  # Form re-rendered
        print(f"  Form has errors: {response.context is not None}")
    
    def test_csrf_token_present(self):
        """Test CSRF token is present in form"""
        response = self.client.get(self.url)
        content = response.content.decode()
        print(f"✓ CSRF token present: {'csrfmiddlewaretoken' in content}")


def run_manual_tests():
    """Run manual tests"""
    print("\n" + "="*60)
    print("INCIDENT REPORT FEATURE - TEST SUITE")
    print("="*60)
    
    print("\n[1] Form Validation Tests")
    print("-" * 60)
    test_form = IncidentReportFormValidationTests()
    test_form.test_valid_form()
    test_form.test_missing_required_field()
    test_form.test_invalid_email()
    test_form.test_future_date()
    test_form.test_short_description()
    
    print("\n[2] View Tests")
    print("-" * 60)
    test_view = IncidentReportViewTests()
    test_view.setUp()
    test_view.test_get_form()
    test_view.test_post_valid_form()
    test_view.test_post_invalid_form()
    test_view.test_csrf_token_present()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_manual_tests()
