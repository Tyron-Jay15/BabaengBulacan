#!/usr/bin/env python
"""
Google Maps API Setup Helper Script
This script automates the Google Maps API key configuration for BabaengBulacan
"""

import os
import sys
import webbrowser
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent

def create_env_file(api_key):
    """Create or update .env file with API key"""
    env_path = get_project_root() / '.env'
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
        
        if 'GOOGLE_MAPS_API_KEY' in content:
            # Update existing key
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('GOOGLE_MAPS_API_KEY='):
                    new_lines.append(f'GOOGLE_MAPS_API_KEY={api_key}')
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        else:
            # Add new key
            content += f'\nGOOGLE_MAPS_API_KEY={api_key}'
    else:
        content = f'GOOGLE_MAPS_API_KEY={api_key}'
    
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"✅ .env file created/updated at: {env_path}")

def update_settings():
    """Update Django settings.py to use environment variable"""
    settings_path = get_project_root() / 'projdjango' / 'settings.py'
    
    if not settings_path.exists():
        print(f"❌ Cannot find settings.py at {settings_path}")
        return False
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    # Check if already configured
    if 'GOOGLE_MAPS_API_KEY' in content:
        print("ℹ️  Settings.py already configured for Google Maps API key")
        return True
    
    # Add import if not present
    if 'import os' not in content:
        insert_pos = content.find('import')
        content = content[:insert_pos] + 'import os\n' + content[insert_pos:]
    
    if 'from dotenv import load_dotenv' not in content:
        insert_pos = content.find('import os') + len('import os\n')
        content = content[:insert_pos] + 'from dotenv import load_dotenv\nload_dotenv()\n' + content[insert_pos:]
    
    # Add Google Maps API Key setting
    if 'GOOGLE_MAPS_API_KEY' not in content:
        insert_pos = content.rfind('\n')
        content = content[:insert_pos] + f'\n\n# Google Maps API Key\nGOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY")\n' + content[insert_pos:]
    
    with open(settings_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Settings.py updated")
    return True

def update_template():
    """Update template to use the API key from settings"""
    template_path = get_project_root() / 'projdjango' / 'templates' / 'resources' / 'resource_center.html'
    
    if not template_path.exists():
        print(f"❌ Cannot find resource_center.html at {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Replace the API key placeholder with Django template variable
    old_script = '<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY"></script>'
    new_script = '<script src="https://maps.googleapis.com/maps/api/js?key={{ GOOGLE_MAPS_API_KEY }}"></script>'
    
    if old_script in content:
        content = content.replace(old_script, new_script)
        with open(template_path, 'w') as f:
            f.write(content)
        print(f"✅ Template updated to use environment variable")
        return True
    else:
        print("ℹ️  Template already uses environment variable")
        return True

def open_google_cloud_console():
    """Open Google Cloud Console to create API key"""
    print("\n📱 Opening Google Cloud Console...")
    print("Steps to follow:")
    print("1. Create a new project (or select existing)")
    print("2. Enable 'Maps JavaScript API'")
    print("3. Create an API key in Credentials")
    print("4. Copy the key and paste it when prompted")
    print("\nOpening browser in 3 seconds...\n")
    
    webbrowser.open('https://console.cloud.google.com/')

def main():
    print("=" * 60)
    print("🗺️  Google Maps API Setup for BabaengBulacan")
    print("=" * 60)
    print()
    
    # Step 1: Open Google Cloud Console
    print("STEP 1: Create Google Cloud Project & API Key")
    print("-" * 60)
    response = input("Do you have a Google Maps API key already? (yes/no): ").strip().lower()
    
    if response != 'yes' and response != 'y':
        open_google_cloud_console()
        input("Press Enter when you have copied your API key from Google Cloud Console...")
    
    # Step 2: Get API key from user
    print("\nSTEP 2: Enter Your API Key")
    print("-" * 60)
    api_key = input("Paste your Google Maps API key here: ").strip()
    
    if not api_key or len(api_key) < 20:
        print("❌ Invalid API key. Please enter a valid Google Maps API key.")
        sys.exit(1)
    
    # Step 3: Setup configuration
    print("\nSTEP 3: Configuring Django Project")
    print("-" * 60)
    
    # Install python-dotenv if needed
    try:
        import dotenv
    except ImportError:
        print("Installing python-dotenv...")
        os.system('pip install python-dotenv')
    
    # Create/update .env file
    create_env_file(api_key)
    
    # Update settings.py
    update_settings()
    
    # Update template
    update_template()
    
    # Step 4: Done
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    print("2. Go to: http://localhost:8000/resources/")
    print("3. Click 'View Map' buttons to test")
    print("\nYour API key is stored in: .env")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
