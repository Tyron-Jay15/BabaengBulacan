#!/usr/bin/env python
"""Test script to verify CAPTCHA generation"""

import os
import sys
import django

# Add the project to the path
sys.path.insert(0, 'c:\\Users\\tyron\\OneDrive\\Desktop\\ProjDjango\\projdjango')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projdjango.settings')
django.setup()

from projdjango.views import generate_captcha_challenge

# Test CAPTCHA generation
print("Testing CAPTCHA generation...")
try:
    captcha = generate_captcha_challenge()
    if captcha:
        print(f"✓ CAPTCHA generated successfully!")
        print(f"  Session ID: {captcha['session_id']}")
        print(f"  Category: {captcha['category']}")
        print(f"  Label: {captcha['label']}")
        print(f"  Number of images: {len(captcha['images'])}")
        if captcha['images']:
            print(f"  First image URL: {captcha['images'][0][:50]}...")
        print(f"\n✓ All tests passed!")
    else:
        print("✗ CAPTCHA generation failed - returned None")
except Exception as e:
    print(f"✗ Error during CAPTCHA generation: {e}")
    import traceback
    traceback.print_exc()
