import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, 'c:\\Users\\tyron\\OneDrive\\Desktop\\ProjDjango\\projdjango')
sys.path.insert(0, 'c:\\Users\\tyron\\OneDrive\\Desktop\\ProjDjango')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projdjango.settings')
django.setup()

from projdjango.models import UserProfile
from django.contrib.auth.models import User

user = User.objects.filter(username='test@example.com').first()
if user:
    try:
        profile = UserProfile.objects.get(user=user)
        encoding = profile.get_face_encoding()
        print(f'User exists: {user.username}')
        print(f'Profile exists: True')
        print(f'Face encoding exists: {encoding is not None}')
        if encoding is not None:
            print(f'Encoding shape: {encoding.shape if hasattr(encoding, "shape") else "no shape"}')
            print(f'Encoding type: {type(encoding)}')
        else:
            print('Face encoding is None')
    except UserProfile.DoesNotExist:
        print('UserProfile does not exist for this user')
else:
    print('Test user does not exist')