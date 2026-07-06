import os
import sys
import django

# Add the project root to the path so Django can find settings
sys.path.insert(0, 'c:\\Users\\tyron\\OneDrive\\Desktop\\ProjDjango\\projdjango')
sys.path.insert(0, 'c:\\Users\\tyron\\OneDrive\\Desktop\\ProjDjango')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projdjango.settings')
django.setup()

from django.contrib.auth.models import User

# Check if test user exists
test_user = User.objects.filter(username='test@example.com').first()

if test_user:
    print(f"Test user already exists: {test_user.username}")
else:
    User.objects.create_user(username='test@example.com', email='test@example.com', password='testpass123')
    print("Test user created: test@example.com")

print("\nTest credentials for login:")
print("Email: test@example.com")
print("Password: testpass123")
