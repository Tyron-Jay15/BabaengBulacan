# Google Maps Setup Guide - Step by Step

Follow these steps to set up Google Maps for the Service Directory feature in your Django project.

## Step 1: Create a Google Cloud Project

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Click on the project dropdown at the top
3. Click **"NEW PROJECT"** button
4. Enter a project name: `BabaengBulacan` (or any name you prefer)
5. Click **"CREATE"**
6. Wait for the project to be created (this may take a few seconds)
7. Once created, the new project will be automatically selected

## Step 2: Enable Google Maps JavaScript API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
   - Or search for "Maps JavaScript API"
2. In the search box, type: `Maps JavaScript API`
3. Click on **Maps JavaScript API** from the results
4. Click the **"ENABLE"** button
5. Wait for it to be enabled (you should see a checkmark)

## Step 3: Create an API Key

1. Go to **APIs & Services** > **Credentials**
   - Or click on "Credentials" in the left sidebar
2. Click **"+ CREATE CREDENTIALS"** button (top left)
3. Select **"API Key"** from the dropdown
4. A dialog will appear with your new API key
5. Copy the API key to your clipboard (it looks like: `AIzaSyD...`)
6. Click **"CLOSE"**

## Step 4: Add the API Key to Your Django Project

### Option A: Direct Edit (Development Only)

1. Open the file: `projdjango/templates/resources/resource_center.html`
2. Find this line (around line 220-225):
   ```html
   <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY"></script>
   ```
3. Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual API key from Step 3
4. Save the file
5. Example (with fake key):
   ```html
   <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD2VJ7wWj7z8k9L0m1N2o3P4q5R6s7T8u9V"></script>
   ```

### Option B: Using Environment Variables (Recommended for Production)

1. Open `projdjango/settings.py`
2. Add this line near the top:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   ```
3. Add this line in your settings:
   ```python
   GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')
   ```
4. Create a `.env` file in your project root (same directory as manage.py):
   ```
   GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   ```
5. Update the script tag in `resource_center.html`:
   ```html
   <script src="https://maps.googleapis.com/maps/api/js?key={{ GOOGLE_MAPS_API_KEY }}"></script>
   ```
6. Update your view to pass the API key to the template:
   ```python
   context = {
       'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY
   }
   ```

## Step 5: Test the Maps Feature

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```
2. Open your browser and go to: `http://localhost:8000/resources/`
3. Scroll down to the **Service Directory** section
4. Click on any **"View Map"** button
5. The map modal should appear with markers showing locations

### Expected Results:
- ✅ Map appears in the modal
- ✅ Markers show for PNP Stations, Shelters, or Counseling Centers
- ✅ Clicking markers shows location name, address, and phone
- ✅ "Get Directions" link works

### Troubleshooting:
- If the map doesn't appear, check the browser console (F12 > Console tab) for errors
- Common error: "Google Maps API key not valid" - double-check you copied the key correctly
- Another error: "API key not enabled for Maps JavaScript API" - go back to Step 2 and enable the API

## Step 6: Set API Key Restrictions (Production)

1. Go back to **APIs & Services** > **Credentials** in Google Cloud Console
2. Click on your API key
3. Scroll down to **API restrictions**
4. Click **"Restrict key"** and select **"Maps JavaScript API"**
5. Scroll down to **Application restrictions**
6. Select **"HTTP referrers (web sites)"**
7. Add your domain(s):
   ```
   *.babaengbulacan.com
   babaengbulacan.com
   localhost:8000
   ```
8. Click **"SAVE"**

## Step 7: Enable Billing (If Needed)

**Note**: Google Maps API usage may be free if your requests stay within the free tier limits. However, Google may require a billing account to be set up.

1. Go to **Billing** in Google Cloud Console
2. If no billing account exists, click **"CREATE BILLING ACCOUNT"**
3. Follow the prompts to add a payment method
4. Link your project to the billing account
5. Set up a budget alert if desired to avoid unexpected charges

## Features That Are Now Active:

✅ **Service Directory with Interactive Maps**
- View PNP Women's Desks locations
- View Emergency Shelters & Safe Houses
- View Counseling Centers

✅ **Map Features**
- Click markers to see location details
- Get real directions via Google Maps
- Auto-centered map for all locations

## Support Links:

- Google Maps API Documentation: https://developers.google.com/maps/documentation
- Google Cloud Console: https://console.cloud.google.com/
- Django Environment Variables: https://django-environ.readthedocs.io/

---

## Quick Checklist:

- [ ] Created Google Cloud Project
- [ ] Enabled Maps JavaScript API
- [ ] Generated API Key
- [ ] Added API Key to resource_center.html
- [ ] Tested maps feature in browser
- [ ] Set API key restrictions (for production)
- [ ] Set up billing account (if required)
- [ ] Maps working with markers and info windows

**Once all checkboxes are complete, your Service Directory maps are fully functional!**
