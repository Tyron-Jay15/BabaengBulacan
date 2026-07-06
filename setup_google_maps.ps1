# Google Maps Setup Helper Script for PowerShell
# This script automates the Google Maps API key configuration

Write-Host "====================================================`n" -ForegroundColor Cyan
Write-Host "   🗺️  Google Maps API Setup for BabaengBulacan`n" -ForegroundColor Cyan
Write-Host "====================================================`n" -ForegroundColor Cyan

Write-Host "Opening Google Cloud Console...`n" -ForegroundColor Yellow
Write-Host "Steps to follow:" -ForegroundColor Green
Write-Host "1. Create a new project or select existing"
Write-Host "2. Enable 'Maps JavaScript API'"
Write-Host "3. Create an API key in Credentials section"
Write-Host "4. Copy the key and paste it when prompted`n"

Read-Host "Press Enter to open Google Cloud Console"

Start-Process "https://console.cloud.google.com/"

Write-Host "Waiting for you to generate the API key...`n" -ForegroundColor Yellow
Read-Host "Press Enter when you have your API key copied"

Write-Host "`n"
$apiKey = Read-Host "Paste your Google Maps API key here"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "ERROR: No API key provided" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nInstalling required Python package (python-dotenv)..." -ForegroundColor Yellow
pip install python-dotenv

Write-Host "`nCreating/updating .env file..." -ForegroundColor Yellow

$envContent = "GOOGLE_MAPS_API_KEY=$apiKey"
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "`n====================================================`n" -ForegroundColor Green
Write-Host "   ✅ SETUP COMPLETE!`n" -ForegroundColor Green
Write-Host "====================================================`n" -ForegroundColor Green

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: python manage.py runserver"
Write-Host "2. Go to: http://localhost:8000/resources/"
Write-Host "3. Click 'View Map' buttons to test`n"
Write-Host "API key stored in: .env" -ForegroundColor Yellow
Write-Host "====================================================`n" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
