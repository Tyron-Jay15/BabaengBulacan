@echo off
REM Google Maps Setup Helper Script for Windows
REM This script automates the Google Maps API key configuration

echo.
echo ====================================================
echo   Google Maps API Setup for BabaengBulacan
echo ====================================================
echo.
echo Opening Google Cloud Console...
echo.
echo Steps to follow:
echo 1. Create a new project or select existing
echo 2. Enable "Maps JavaScript API"
echo 3. Create an API key in Credentials section
echo 4. Copy the key and paste it when prompted
echo.
echo Press any key to open Google Cloud Console...
pause >nul

start https://console.cloud.google.com/

echo.
echo Waiting for you to generate the API key...
echo Press any key when you have your API key copied...
pause >nul

echo.
set /p API_KEY="Paste your Google Maps API key here: "

if "%API_KEY%"=="" (
    echo ERROR: No API key provided
    pause
    exit /b 1
)

echo.
echo Installing required Python package (python-dotenv)...
pip install python-dotenv

echo.
echo Creating/updating .env file...

(
    echo GOOGLE_MAPS_API_KEY=%API_KEY%
) > .env

echo.
echo ====================================================
echo   SETUP COMPLETE!
echo ====================================================
echo.
echo Next steps:
echo 1. Run: python manage.py runserver
echo 2. Go to: http://localhost:8000/resources/
echo 3. Click "View Map" buttons to test
echo.
echo API key stored in: .env
echo ====================================================
echo.
pause
