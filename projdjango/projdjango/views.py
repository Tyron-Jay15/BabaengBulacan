"""
Views for BabaengBulacan application
"""
import logging
from typing import Optional, Tuple
import uuid

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt

import base64
import io
import json
import random
import requests
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

from .models import (
    UserProfile, IncidentReport, EmailVerificationToken, PasswordResetToken,
    TwoFactorAuth, AuthenticationLog,
)
from .forms import IncidentReportForm
from . import emails as auth_emails
from . import security

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
FACE_DISTANCE_THRESHOLD = 0.6
BUSINESS_HOURS_START = getattr(settings, 'BUSINESS_HOURS_START', 6)
BUSINESS_HOURS_END = getattr(settings, 'BUSINESS_HOURS_END', 22)
ALLOW_EMERGENCY_ACCESS = getattr(settings, 'ALLOW_EMERGENCY_ACCESS', True)
PASSWORD_MIN_LENGTH = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
PASSWORD_REQUIRE_UPPERCASE = getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True)
PASSWORD_REQUIRE_LOWERCASE = getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True)
PASSWORD_REQUIRE_DIGIT = getattr(settings, 'PASSWORD_REQUIRE_DIGIT', True)
PASSWORD_REQUIRE_SPECIAL = getattr(settings, 'PASSWORD_REQUIRE_SPECIAL', True)

# CAPTCHA image categories and properties
CAPTCHA_CATEGORIES = {
    'cars': {'label': 'Select all cars', 'color_range': [(0, 0, 100), (255, 100, 100)], 'symbol': '🚗'},
    'bikes': {'label': 'Select all bicycles', 'color_range': [(0, 100, 0), (100, 255, 100)], 'symbol': '🚲'},
    'trees': {'label': 'Select all trees', 'color_range': [(0, 100, 0), (100, 200, 100)], 'symbol': '🌳'},
    'houses': {'label': 'Select all houses', 'color_range': [(100, 50, 0), (200, 150, 100)], 'symbol': '🏠'},
    'clouds': {'label': 'Select all clouds', 'color_range': [(200, 200, 200), (255, 255, 255)], 'symbol': '☁️'},
    'fire': {'label': 'Select all fire', 'color_range': [(0, 0, 200), (255, 200, 0)], 'symbol': '🔥'},
}


def get_unsplash_image(query: str) -> Optional[str]:
    """
    Fetch a real image from Unsplash API.
    
    Args:
        query: Search query for image
        
    Returns:
        Image URL or placeholder
    """
    try:
        # Use Lorem Picsum (free placeholder service) with random images
        seed = random.randint(1000, 9999)
        return f"https://picsum.photos/150/150?random={seed}"
    except Exception as e:
        logger.debug(f"Error generating image: {e}")
        return None


def generate_placeholder_image(query: str, is_match: bool) -> str:
    """
    Generate a placeholder image URL.
    
    Args:
        query: Image category
        is_match: Whether this image should match the category
        
    Returns:
        Image URL
    """
    try:
        # Use Lorem Picsum (free placeholder service)
        seed = random.randint(1000, 9999)
        return f"https://picsum.photos/150/150?random={seed}"
    except Exception as e:
        logger.debug(f"Error generating placeholder image: {e}")
        return f"https://picsum.photos/150/150?random=1000"


def generate_captcha_challenge() -> dict:
    """
    Generate a complete CAPTCHA challenge with real images.
    
    Returns:
        Dictionary with challenge data
    """
    try:
        import uuid
        from django.core.cache import cache
        
        # Select random category
        category = random.choice(list(CAPTCHA_CATEGORIES.keys()))
        category_data = CAPTCHA_CATEGORIES[category]
        
        # Generate 9 images (3x3 grid like Google)
        images = []
        correct_indices = []
        
        for idx in range(9):
            # Randomly decide if this image matches the category (50% chance)
            is_match = random.choice([True, False])
            
            # Get placeholder image URL
            img_data = generate_placeholder_image(category, is_match)
            if not img_data:
                img_data = f"https://picsum.photos/150/150?random={random.randint(1000, 9999)}"
            
            images.append(img_data)
            if is_match:
                correct_indices.append(idx)
        
        # Ensure at least 2 correct images
        if len(correct_indices) < 2:
            correct_indices = [0, 4]  # Default if random generation didn't work
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Cache the correct answer for validation
        cache_data = {
            'category': category,
            'correct_indices': correct_indices,
            'created_at': timezone.now().timestamp()
        }
        cache.set(f'captcha_{session_id}', cache_data, timeout=300)  # 5 minutes
        
        return {
            'session_id': session_id,
            'images': images,
            'label': category_data['label'],
            'category': category
        }
    except Exception as e:
        logger.error(f"Error generating CAPTCHA challenge: {e}")
        return None


def decode_base64_image(base64_string: str) -> Optional[np.ndarray]:
    """
    Decode base64 image string to numpy array.

    Args:
        base64_string: Base64 encoded image string, possibly with data URL prefix.

    Returns:
        Numpy array representing the image, or None if decoding fails.
    """
    try:
        logger.debug(f"Decoding base64 image, length: {len(base64_string)}")
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
            logger.debug(f"After removing prefix, length: {len(base64_string)}")

        image_data = base64.b64decode(base64_string)
        logger.debug(f"Decoded bytes length: {len(image_data)}")
        image = Image.open(io.BytesIO(image_data))
        logger.debug(f"PIL image size: {image.size}, mode: {image.mode}")
        if CV2_AVAILABLE and NUMPY_AVAILABLE:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.debug(f"OpenCV image shape: {cv_image.shape}")
            return cv_image
        if NUMPY_AVAILABLE:
            return np.array(image)
        return image
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None


def get_face_encoding(image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Extract face encoding from image.

    Args:
        image: Numpy array of the image.

    Returns:
        Tuple of (face_encoding, error_message). Face_encoding is None if error.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        # Mock implementation - just return a dummy encoding for any valid image
        if image is not None and getattr(image, 'size', 0):
            if NUMPY_AVAILABLE:
                return np.random.rand(128).astype(np.float64), None
            return [random.random() for _ in range(128)], None
        return None, "Invalid image"

    if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
        return None, "Face recognition libraries are not installed on this server"

    try:
        # Convert to RGB for face_recognition
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Find faces
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            return None, "No face detected in the image"

        if len(face_locations) > 1:
            return None, "Multiple faces detected. Please ensure only one face is visible"

        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if face_encodings:
            return face_encodings[0], None
        else:
            return None, "Could not encode face"
    except Exception as e:
        logger.error(f"Error processing face: {e}")
        return None, f"Error processing face: {str(e)}"


def verify_face(known_encoding: np.ndarray, image: np.ndarray) -> Tuple[bool, Optional[str]]:
    """
    Verify if face in image matches known encoding.

    Args:
        known_encoding: Known face encoding.
        image: Numpy array of the image to verify.

    Returns:
        Tuple of (is_match, error_message).
    """
    logger.debug(f"verify_face called with image: {image is not None}")
    if image is not None:
        logger.debug(f"Image shape: {image.shape}, dtype: {image.dtype}")

    if not FACE_RECOGNITION_AVAILABLE:
        # Mock implementation - always return success for demo
        logger.debug("Using mock face verification - ALWAYS SUCCESS")
        return True, None

    if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
        return False, "Face recognition libraries are not installed on this server"

    try:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        if not face_locations:
            return False, "No face detected"

        if len(face_locations) > 1:
            return False, "Multiple faces detected"

        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if not face_encodings:
            return False, "Could not encode face"

        # Compare faces
        matches = face_recognition.compare_faces([known_encoding], face_encodings[0])
        face_distance = face_recognition.face_distance([known_encoding], face_encodings[0])

        if matches[0] and face_distance[0] < FACE_DISTANCE_THRESHOLD:
            return True, None
        else:
            return False, "Face does not match"
    except Exception as e:
        logger.error(f"Error verifying face: {e}")
        return False, f"Error verifying face: {str(e)}"


def is_business_hours() -> bool:
    """
    Check if current time is within business hours.

    Returns:
        True if within business hours or emergency access allowed.
    """
    if ALLOW_EMERGENCY_ACCESS:
        return True
    current_hour = timezone.now().hour
    return BUSINESS_HOURS_START <= current_hour < BUSINESS_HOURS_END


def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password strength based on settings.

    Args:
        password: Password to validate.

    Returns:
        Error message if invalid, None if valid.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return f'Password must be at least {PASSWORD_MIN_LENGTH} characters long.'

    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return 'Password must contain at least one uppercase letter.'

    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return 'Password must contain at least one lowercase letter.'

    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return 'Password must contain at least one digit.'

    if PASSWORD_REQUIRE_SPECIAL and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in password):
        return 'Password must contain at least one special character.'

    return None


def verify_recaptcha(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify reCAPTCHA token with Google's verification API.
    
    Args:
        token: reCAPTCHA token from the client
        
    Returns:
        Tuple of (is_valid, error_message). is_valid is True if verification passed.
    """
    try:
        recaptcha_secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
        recaptcha_api_url = getattr(settings, 'RECAPTCHA_API_URL', 'https://www.google.com/recaptcha/api/siteverify')
        
        if not recaptcha_secret:
            # No secret configured -> CAPTCHA disabled (e.g. local dev). Allow through.
            logger.warning("RECAPTCHA_SECRET_KEY not configured; skipping CAPTCHA check")
            return True, None
        
        response = requests.post(
            recaptcha_api_url,
            data={
                'secret': recaptcha_secret,
                'response': token
            },
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"reCAPTCHA API returned status {response.status_code}")
            return False, "Failed to verify reCAPTCHA"
        
        result = response.json()
        
        if result.get('success'):
            return True, None
        else:
            error_codes = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA verification failed with errors: {error_codes}")
            return False, "reCAPTCHA verification failed"
    
    except requests.exceptions.Timeout:
        logger.error("reCAPTCHA API request timed out")
        return False, "reCAPTCHA verification timed out"
    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA: {e}")
        return False, f"Error verifying reCAPTCHA: {str(e)}"


def captcha_passed(request) -> bool:
    """Validate the reCAPTCHA response submitted with a POST request."""
    from projdjango.recaptcha_utils import captcha_required_for_request

    if not captcha_required_for_request(request):
        return True

    token = request.POST.get('g-recaptcha-response', '').strip()
    if not token:
        return False
    is_valid, _ = verify_recaptcha(token)
    return is_valid


def _within_business_hours() -> Tuple[bool, str]:
    """Return (allowed, message). Honors ALLOW_EMERGENCY_ACCESS."""
    allow_emergency = getattr(settings, 'ALLOW_EMERGENCY_ACCESS', True)
    if allow_emergency:
        return True, ''
    start = getattr(settings, 'BUSINESS_HOURS_START', 6)
    end = getattr(settings, 'BUSINESS_HOURS_END', 22)
    current_hour = timezone.now().hour
    if start <= current_hour < end:
        return True, ''
    return False, (f'This service is only available during business hours '
                   f'({start}:00 - {end}:00). For emergencies, please contact support.')


def create_email_verification(user, request=None):
    """Create a fresh email verification token, email it, and return (token, link)."""
    ttl = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_TTL', 86400)
    EmailVerificationToken.objects.filter(user=user, used=False).update(used=True)
    token = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(seconds=ttl),
        ip_address=security.get_client_ip(request) if request else None,
    )
    sent, link = auth_emails.send_verification_email(user, token.token, request)
    return token, link, sent


def _uses_console_email():
    return 'console' in getattr(settings, 'EMAIL_BACKEND', '').lower()


def _admin_verification_required():
    return getattr(settings, 'ADMIN_EMAIL_VERIFICATION', True)


def _registration_pending_context(email, **extra):
    """Context when accounts must be approved by an administrator."""
    return {
        'email': email,
        'admin_verification': True,
        **extra,
    }


def _verification_sent_context(email, verify_link, email_sent, **extra):
    """Build template context for the post-registration verification page."""
    if _admin_verification_required():
        return _registration_pending_context(email, **extra)

    smtp_ready = getattr(settings, 'SMTP_CONFIGURED', False)
    show_on_page_link = bool(verify_link) and (not smtp_ready or not email_sent)
    ctx = {
        'email': email,
        'verify_link': verify_link,
        'email_sent': email_sent,
        'smtp_configured': smtp_ready,
        'show_on_page_link': show_on_page_link,
        'admin_verification': False,
        'show_dev_link': settings.DEBUG or _uses_console_email(),
    }
    ctx.update(extra)
    return ctx


def create_password_reset(user, request=None):
    """Create a fresh password reset token and email it to the user."""
    ttl = getattr(settings, 'PASSWORD_RESET_TOKEN_TTL', 3600)
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(seconds=ttl),
        ip_address=security.get_client_ip(request) if request else None,
    )
    auth_emails.send_password_reset_email(user, token.token, request)
    return token


def get_login_redirect_name(user):
    """Return URL name for post-login redirect based on database role."""
    if user.is_staff or user.is_superuser:
        return 'admin_dashboard'
    return 'user_dashboard'


def complete_login(request, user, auth_method='password+face'):
    """
    Finalise a successful authentication: reset counters, log the user in,
    handle new-device detection/notification, write the audit log, and return
    a redirect response (with the device-recognition cookie attached).
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.record_successful_login()
    security.reset_rate_limit(request)

    # Device recognition (new-device email alert)
    device_token = security.get_device_token(request)
    is_new_device = not security.is_known_device(user, device_token)

    auth_login(request, user)

    response = redirect(get_login_redirect_name(user))
    if not device_token:
        device_token = security.new_device_token()
        security.set_device_cookie(response, device_token)
    security.remember_device(user, device_token, request)

    security.log_auth_event(request, 'login_success', user=user, auth_method=auth_method)
    if is_new_device:
        security.log_auth_event(request, 'new_device', user=user, auth_method=auth_method,
                                details='Login from a new device/browser')
        auth_emails.send_new_device_notification(user, request)

    return response


def _is_staff_account(user):
    return user.is_staff or user.is_superuser


def _portal_login_url(portal):
    return reverse('admin_login') if portal == 'admin' else reverse('login')


def _handle_failed_login_attempt(request, user, profile, email, reason=''):
    security.record_failed_login(request, username_attempted=email, user=user, reason=reason)
    just_locked = profile.record_failed_attempt()
    security.log_auth_event(request, 'login_failed', user=user, success=False, details=reason)
    if just_locked:
        minutes = getattr(settings, 'LOCKOUT_DURATION', 900) // 60
        security.log_auth_event(request, 'account_locked', user=user, success=False,
                                details='Locked after repeated failures')
        auth_emails.send_account_locked_notification(user, request, minutes=minutes)


def _authenticate_login_portal(request, email, password, portal, template_name):
    """
    Shared credential checks for resident and admin login portals.

    portal: 'resident' | 'admin'
    Returns (auth_user, profile, error_response) — error_response is a rendered HttpResponse when set.
    """
    def fail(message, **extra):
        ctx = {'error': message, 'email': email}
        ctx.update(extra)
        return None, None, render(request, template_name, ctx)

    allowed, message = _within_business_hours()
    if not allowed:
        return fail(message)

    if security.is_rate_limited(request):
        security.record_failed_login(request, username_attempted=email, reason='rate_limited')
        return fail('Too many login attempts from your network. Please wait a few minutes and try again.')

    security.register_login_attempt(request)

    if not captcha_passed(request):
        return fail('reCAPTCHA verification failed. Please try again.')

    user = User.objects.filter(email__iexact=email).order_by(
        '-is_superuser', '-is_staff', '-date_joined',
    ).first()
    if user is None:
        security.record_failed_login(request, username_attempted=email, reason='unknown_user')
        security.log_auth_event(request, 'login_failed', success=False,
                                username_attempted=email, details='Unknown email')
        return fail('Invalid email or password.')

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if portal == 'admin' and not _is_staff_account(user):
        security.record_failed_login(request, username_attempted=email, user=user, reason='not_staff')
        security.log_auth_event(request, 'login_failed', user=user, success=False,
                                details='Non-staff attempted admin login')
        return fail('Invalid email or password.')

    if profile.is_locked_out():
        remaining = profile.get_remaining_lockout_time()
        return fail(
            f'Account is temporarily locked due to too many failed attempts. '
            f'Try again in {remaining // 60}:{remaining % 60:02d}.'
        )

    auth_user = authenticate(request, username=user.username, password=password)
    if auth_user is None:
        _handle_failed_login_attempt(request, user, profile, email, reason='bad_password')
        return fail('Invalid email or password.')

    if portal == 'resident' and _is_staff_account(auth_user):
        security.log_auth_event(request, 'login_failed', user=user, success=False,
                                details='Staff attempted resident login')
        return fail(
            'Administrator accounts must use the staff login page.',
            admin_login_hint=True,
        )

    if not profile.email_verified:
        security.log_auth_event(request, 'login_failed', user=user, success=False,
                                details='Account not approved')
        if _admin_verification_required():
            return fail(
                'Your account is pending administrator approval. '
                'You will be able to sign in after an admin verifies your registration.',
                pending_admin=True,
            )
        return fail(
            'Please verify your email address before signing in. Check your inbox for the verification link.',
            show_resend=True,
        )

    return auth_user, profile, None


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(View):
    """Resident login — face verification required; staff accounts are not accepted."""

    def get(self, request):
        if request.user.is_authenticated:
            if _is_staff_account(request.user):
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
        return render(request, 'accounts/login.html')

    def _fail(self, request, email, message, **extra):
        ctx = {'error': message, 'email': email}
        ctx.update(extra)
        return render(request, 'accounts/login.html', ctx)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        face_image = request.POST.get('face_image', '').strip()

        auth_user, profile, error_response = _authenticate_login_portal(
            request, email, password, 'resident', 'accounts/login.html',
        )
        if error_response is not None:
            return error_response

        face_error = self._verify_face_step(face_image, profile, auth_user, request)
        if face_error:
            _handle_failed_login_attempt(request, auth_user, profile, email, reason='face_failed')
            return self._fail(request, email, face_error)

        request.session['login_portal'] = 'resident'
        if profile.has_2fa_enabled:
            request.session['pending_2fa_user_id'] = auth_user.id
            request.session['pending_2fa_ts'] = timezone.now().isoformat()
            return redirect('two_factor_verify')

        return complete_login(request, auth_user, auth_method='password+face')

    def _verify_face_step(self, face_image, profile, user, request=None):
        """Returns an error string if face verification fails, else None."""
        from projdjango.recaptcha_utils import is_mobile_lan_dev_access

        request = request or getattr(self, 'request', None)
        stored_encoding = profile.get_face_encoding()
        if not face_image:
            if (
                request
                and is_mobile_lan_dev_access(request)
                and not getattr(settings, 'FACE_ENFORCE_ON_LAN', False)
            ):
                return None
            return 'Face verification is required. On mobile over Wi-Fi, use HTTPS or tap Login without face if enabled.'
        image = decode_base64_image(face_image)
        if image is None:
            return 'Invalid face image. Please try again.'
        if stored_encoding is None:
            return 'Face data not found. Please contact support or re-register with face capture.'
        is_match, error = verify_face(stored_encoding, image)
        if not is_match:
            return f'Face verification failed: {error}'
        return None


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class AdminLoginView(View):
    """Staff-only login portal — password (+ optional 2FA); no face verification."""

    def get(self, request):
        if request.user.is_authenticated:
            if _is_staff_account(request.user):
                return redirect('admin_dashboard')
            auth_logout(request)
        return render(request, 'accounts/admin_login.html')

    def _fail(self, request, email, message):
        return render(request, 'accounts/admin_login.html', {'error': message, 'email': email})

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        auth_user, profile, error_response = _authenticate_login_portal(
            request, email, password, 'admin', 'accounts/admin_login.html',
        )
        if error_response is not None:
            return error_response

        request.session['login_portal'] = 'admin'
        if profile.has_2fa_enabled:
            request.session['pending_2fa_user_id'] = auth_user.id
            request.session['pending_2fa_ts'] = timezone.now().isoformat()
            return redirect('two_factor_verify')

        return complete_login(request, auth_user, auth_method='password')


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(View):
    """Handle user registration"""
    
    def get(self, request):
        """Render registration page"""
        return render(request, 'accounts/register.html')
    
    def post(self, request):
        """Handle registration form submission"""
        # Check business hours (unless emergency access is allowed)
        current_hour = timezone.now().hour
        business_start = getattr(settings, 'BUSINESS_HOURS_START', 6)
        business_end = getattr(settings, 'BUSINESS_HOURS_END', 22)
        allow_emergency = getattr(settings, 'ALLOW_EMERGENCY_ACCESS', True)
        
        if not allow_emergency and not (business_start <= current_hour < business_end):
            return render(request, 'accounts/register.html', {
                'error': f'Registration is only available during business hours ({business_start}:00 - {business_end}:00). For emergencies, please contact support.',
                'name': request.POST.get('name', ''),
                'email': request.POST.get('email', ''),
            })
        
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        face_image = request.POST.get('face_image', '').strip()
        
        # Verify reCAPTCHA
        if not captcha_passed(request):
            return render(request, 'accounts/register.html', {
                'error': 'reCAPTCHA verification failed. Please try again.',
                'name': name,
                'email': email,
            })
        
        # Validate input
        if not all([name, email, password, confirm_password]):
            captcha = generate_captcha_challenge()
            return render(request, 'accounts/register.html', {
                'error': 'All fields are required.',
                'captcha': captcha
            })
        
        if password != confirm_password:
            captcha = generate_captcha_challenge()
            return render(request, 'accounts/register.html', {
                'error': 'Passwords do not match.',
                'name': name,
                'email': email,
                'captcha': captcha
            })
        
        # Validate password strength
        min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
        require_upper = getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True)
        require_lower = getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True)
        require_digit = getattr(settings, 'PASSWORD_REQUIRE_DIGIT', True)
        require_special = getattr(settings, 'PASSWORD_REQUIRE_SPECIAL', True)
        
        if len(password) < min_length:
            return render(request, 'accounts/register.html', {
                'error': f'Password must be at least {min_length} characters long.',
                'name': name,
                'email': email,
            })
        
        if require_upper and not any(c.isupper() for c in password):
            return render(request, 'accounts/register.html', {
                'error': 'Password must contain at least one uppercase letter.',
                'name': name,
                'email': email,
            })
        
        if require_lower and not any(c.islower() for c in password):
            return render(request, 'accounts/register.html', {
                'error': 'Password must contain at least one lowercase letter.',
                'name': name,
                'email': email,
            })
        
        if require_digit and not any(c.isdigit() for c in password):
            return render(request, 'accounts/register.html', {
                'error': 'Password must contain at least one digit.',
                'name': name,
                'email': email,
            })
        
        if require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in password):
            return render(request, 'accounts/register.html', {
                'error': 'Password must contain at least one special character.',
                'name': name,
                'email': email,
            })
        
        # Check if user exists
        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Email already registered.',
                'name': name,
            })
        
        # Process face recognition
        if not face_image:
            return render(request, 'accounts/register.html', {
                'error': 'Face capture is required for registration.',
                'name': name,
                'email': email,
            })
        
        image = decode_base64_image(face_image)
        if image is None:
            return render(request, 'accounts/register.html', {
                'error': 'Invalid face image. Please try again.',
                'name': name,
                'email': email,
            })
        
        face_encoding, error = get_face_encoding(image)
        if error:
            return render(request, 'accounts/register.html', {
                'error': f'Face recognition error: {error}',
                'name': name,
                'email': email,
            })
        
        # Create user (account starts unverified; email verification is required)
        try:
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
            )

            # Store face encoding on the auto-created profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.set_face_encoding(face_encoding)
            profile.save_face_photo_from_base64(face_image)
            profile.save(update_fields=['face_photo'])

            if _admin_verification_required():
                security.log_auth_event(request, 'register', user=user,
                                        details='Account registered, pending admin approval')
                return render(request, 'accounts/verification_sent.html',
                              _registration_pending_context(email))
            else:
                _token, verify_link, email_sent = create_email_verification(user, request)
                security.log_auth_event(request, 'register', user=user,
                                        details='Account registered, verification email sent')
                return render(request, 'accounts/verification_sent.html', _verification_sent_context(
                    email, verify_link, email_sent,
                ))
        except Exception as e:
            logger.error("Registration failed: %s", e, exc_info=True)
            return render(request, 'accounts/register.html', {
                'error': f'Registration failed: {str(e)}',
                'name': name,
                'email': email,
            })


class LogoutView(View):
    """Handle user logout"""

    @method_decorator(login_required)
    def get(self, request):
        was_staff = _is_staff_account(request.user)
        security.log_auth_event(request, 'logout', user=request.user)
        auth_logout(request)
        if was_staff:
            return redirect('admin_login')
        return redirect('home')


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ForgotPasswordView(View):
    """Handle forgot password requests"""
    
    def get(self, request):
        """Render forgot password page"""
        return render(request, 'accounts/forgot_password.html')
    
    def post(self, request):
        """Handle forgot password form submission"""
        email = request.POST.get('email', '').strip()

        if not email:
            return render(request, 'accounts/forgot_password.html', {
                'error': 'Please enter your email address.'
            })

        if not captcha_passed(request):
            return render(request, 'accounts/forgot_password.html', {
                'error': 'reCAPTCHA verification failed. Please try again.',
            })

        generic_success = (f'If {email} is registered, you will receive password '
                           f'reset instructions shortly.')

        try:
            user = User.objects.get(email__iexact=email)
            create_password_reset(user, request)
            security.log_auth_event(request, 'password_reset_request', user=user,
                                    details='Password reset requested')
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # Don't reveal whether the email exists (anti-enumeration)
            pass

        return render(request, 'accounts/forgot_password.html', {'success': generic_success})


@login_required(login_url='login')
def profile_view(request):
    """Display user profile with security overview (2FA, login history)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    twofa = getattr(request.user, 'two_factor', None)
    recent_logins = AuthenticationLog.objects.filter(
        user=request.user,
        event_type__in=['login_success', 'login_failed', '2fa_success', '2fa_failed', 'new_device', 'logout'],
    )[:15]

    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
        'two_factor_enabled': bool(twofa and twofa.is_enabled),
        'backup_codes_remaining': security.count_unused_backup_codes(request.user),
        'recent_logins': recent_logins,
        'known_devices': request.user.known_devices.all()[:10],
    })


# ===========================================================================
# Email verification
# ===========================================================================
def verify_email(request, token):
    """Confirm a user's email address from the link in the verification email."""
    if _admin_verification_required():
        return render(request, 'accounts/verification_result.html', {
            'success': False,
            'message': 'Self-service email verification is disabled. '
                       'Please wait for an administrator to approve your account, then sign in.',
        })

    try:
        vt = EmailVerificationToken.objects.select_related('user').get(token=token)
    except EmailVerificationToken.DoesNotExist:
        return render(request, 'accounts/verification_result.html', {
            'success': False,
            'message': 'This verification link is invalid. Please request a new one.',
        })

    if not vt.is_valid():
        return render(request, 'accounts/verification_result.html', {
            'success': False,
            'expired': True,
            'email': vt.user.email,
            'message': 'This verification link has expired or was already used.',
        })

    profile, _ = UserProfile.objects.get_or_create(user=vt.user)
    profile.mark_email_verified()
    vt.mark_used()

    security.log_auth_event(request, 'email_verified', user=vt.user, details='Email verified')
    auth_emails.send_email_verified_notification(vt.user)

    return render(request, 'accounts/verification_result.html', {
        'success': True,
        'message': 'Your email has been verified! You can now sign in to your account.',
    })


@csrf_protect
def resend_verification(request):
    """Resend the verification email (POST with `email`) — email mode only."""
    if request.method != 'POST':
        return redirect('login')
    email = request.POST.get('email', '').strip()

    if _admin_verification_required():
        return render(request, 'accounts/verification_sent.html',
                      _registration_pending_context(
                          email,
                          message='Your account is still pending administrator approval.',
                      ))

    generic = ('If that account exists and is not yet verified, a new verification '
               'email has been sent.')
    try:
        user = User.objects.get(email__iexact=email)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        verify_link = None
        email_sent = False
        if not profile.email_verified:
            _, verify_link, email_sent = create_email_verification(user, request)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        verify_link = None
        email_sent = False
    return render(request, 'accounts/verification_sent.html', _verification_sent_context(
        email, verify_link, email_sent,
        resent=True,
        message=generic,
    ))


# ===========================================================================
# Password reset (token-based)
# ===========================================================================
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResetPasswordView(View):
    """Set a new password using a valid reset token."""

    def _get_token(self, token):
        try:
            return PasswordResetToken.objects.select_related('user').get(token=token)
        except PasswordResetToken.DoesNotExist:
            return None

    def get(self, request, token):
        rt = self._get_token(token)
        if not rt or not rt.is_valid():
            return render(request, 'accounts/reset_password.html', {'invalid': True})
        return render(request, 'accounts/reset_password.html', {'token': token})

    def post(self, request, token):
        rt = self._get_token(token)
        if not rt or not rt.is_valid():
            return render(request, 'accounts/reset_password.html', {'invalid': True})

        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()

        if password != confirm:
            return render(request, 'accounts/reset_password.html', {
                'token': token, 'error': 'Passwords do not match.'})

        pw_error = validate_password_strength(password)
        if pw_error:
            return render(request, 'accounts/reset_password.html', {'token': token, 'error': pw_error})

        user = rt.user
        user.set_password(password)
        user.save()
        rt.mark_used()

        # Unlock the account if it was locked, and treat as recovery.
        profile, _ = UserProfile.objects.get_or_create(user=user)
        was_locked = profile.is_locked_out()
        profile.login_attempts = 0
        profile.lockout_until = None
        # A verified-by-email reset also confirms ownership of the address.
        if not profile.email_verified:
            profile.email_verified = True
            profile.email_verified_at = timezone.now()
        profile.save()

        security.log_auth_event(request, 'password_changed', user=user, details='Password reset via email')
        auth_emails.send_password_changed_notification(user, request)
        if was_locked:
            security.log_auth_event(request, 'account_recovered', user=user)
            auth_emails.send_account_recovered_notification(user, request)

        return render(request, 'accounts/reset_password.html', {'done': True})


# ===========================================================================
# Two-Factor Authentication (TOTP)
# ===========================================================================
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class TwoFactorVerifyView(View):
    """Second factor prompt shown after password + face verification."""

    MAX_ATTEMPTS = 5

    def _pending_user(self, request):
        uid = request.session.get('pending_2fa_user_id')
        if not uid:
            return None
        return User.objects.filter(id=uid).first()

    def _portal_login_redirect(self, request, query=''):
        portal = request.session.get('login_portal', 'resident')
        url = _portal_login_url(portal)
        return redirect(url + query)

    def get(self, request):
        user = self._pending_user(request)
        if not user:
            return self._portal_login_redirect(request)
        return render(request, 'accounts/two_factor_verify.html', {
            'admin_portal': request.session.get('login_portal') == 'admin',
        })

    def post(self, request):
        user = self._pending_user(request)
        if not user:
            return self._portal_login_redirect(request)

        code = request.POST.get('code', '').strip()
        use_backup = request.POST.get('use_backup') == '1'
        twofa = getattr(user, 'two_factor', None)

        attempts = request.session.get('twofa_attempts', 0) + 1
        request.session['twofa_attempts'] = attempts

        verified = False
        method = 'totp'
        if use_backup:
            method = 'backup_code'
            verified = security.consume_backup_code(user, code)
        elif twofa:
            verified = security.verify_totp(twofa.get_secret(), code)

        if verified:
            request.session.pop('pending_2fa_user_id', None)
            request.session.pop('pending_2fa_ts', None)
            request.session.pop('twofa_attempts', None)
            portal = request.session.get('login_portal', 'resident')
            if twofa:
                twofa.last_used_at = timezone.now()
                twofa.save(update_fields=['last_used_at'])
            security.log_auth_event(request, '2fa_success', user=user, auth_method=method)
            base = 'password' if portal == 'admin' else 'password+face'
            return complete_login(request, user, auth_method=f'{base}+{method}')

        # Failed
        security.log_auth_event(request, '2fa_failed', user=user, success=False, auth_method=method)
        if attempts >= self.MAX_ATTEMPTS:
            request.session.pop('pending_2fa_user_id', None)
            request.session.pop('twofa_attempts', None)
            return self._portal_login_redirect(request, '?message=Too many invalid codes. Please sign in again.')

        return render(request, 'accounts/two_factor_verify.html', {
            'error': 'Invalid code. Please try again.',
            'use_backup': use_backup,
            'attempts_left': self.MAX_ATTEMPTS - attempts,
            'admin_portal': request.session.get('login_portal') == 'admin',
        })


@login_required(login_url='login')
@csrf_protect
def two_factor_setup(request):
    """Show the QR code / secret to enrol an authenticator app."""
    twofa, _ = TwoFactorAuth.objects.get_or_create(user=request.user)
    if twofa.is_enabled:
        messages.info(request, 'Two-factor authentication is already enabled.')
        return redirect('profile')

    secret = request.session.get('twofa_setup_secret')
    if not secret:
        secret = security.generate_totp_secret()
        request.session['twofa_setup_secret'] = secret

    uri = security.get_totp_provisioning_uri(secret, request.user.email or request.user.username)
    qr_data_uri = security.generate_qr_code_data_uri(uri)

    return render(request, 'accounts/two_factor_setup.html', {
        'secret': secret,
        'qr_data_uri': qr_data_uri,
    })


@login_required(login_url='login')
@csrf_protect
def two_factor_enable(request):
    """Confirm the TOTP code and activate 2FA, returning backup codes."""
    if request.method != 'POST':
        return redirect('two_factor_setup')

    secret = request.session.get('twofa_setup_secret')
    code = request.POST.get('code', '').strip()

    if not secret:
        messages.error(request, 'Your setup session expired. Please start again.')
        return redirect('two_factor_setup')

    if not security.verify_totp(secret, code):
        uri = security.get_totp_provisioning_uri(secret, request.user.email or request.user.username)
        return render(request, 'accounts/two_factor_setup.html', {
            'secret': secret,
            'qr_data_uri': security.generate_qr_code_data_uri(uri),
            'error': 'That code was incorrect. Make sure your device clock is correct and try again.',
        })

    twofa, _ = TwoFactorAuth.objects.get_or_create(user=request.user)
    twofa.set_secret(secret)
    twofa.is_enabled = True
    twofa.confirmed_at = timezone.now()
    twofa.save()

    request.session.pop('twofa_setup_secret', None)
    codes = security.create_backup_codes_for_user(request.user)
    request.session['backup_codes_once'] = codes  # for one-time download

    security.log_auth_event(request, '2fa_enabled', user=request.user)

    return render(request, 'accounts/backup_codes.html', {
        'codes': codes,
        'just_enabled': True,
    })


@login_required(login_url='login')
@csrf_protect
def two_factor_disable(request):
    """Disable 2FA after confirming the user's current password."""
    if request.method != 'POST':
        return redirect('profile')

    password = request.POST.get('password', '').strip()
    if not request.user.check_password(password):
        messages.error(request, 'Incorrect password. Two-factor authentication was not disabled.')
        return redirect('profile')

    twofa = getattr(request.user, 'two_factor', None)
    if twofa:
        twofa.is_enabled = False
        twofa.encrypted_secret = ''
        twofa.confirmed_at = None
        twofa.save()
    from .models import BackupCode
    BackupCode.objects.filter(user=request.user).delete()

    security.log_auth_event(request, '2fa_disabled', user=request.user)
    messages.success(request, 'Two-factor authentication has been disabled.')
    return redirect('profile')


@login_required(login_url='login')
@csrf_protect
def backup_codes_regenerate(request):
    """Generate a fresh set of backup codes (invalidating the old ones)."""
    if request.method != 'POST':
        return redirect('profile')
    twofa = getattr(request.user, 'two_factor', None)
    if not (twofa and twofa.is_enabled):
        messages.error(request, 'Enable two-factor authentication first.')
        return redirect('profile')

    codes = security.create_backup_codes_for_user(request.user)
    request.session['backup_codes_once'] = codes
    return render(request, 'accounts/backup_codes.html', {'codes': codes})


@login_required(login_url='login')
def backup_codes_download(request):
    """Download the most recently generated backup codes as a text file."""
    codes = request.session.get('backup_codes_once')
    if not codes:
        messages.error(request, 'No backup codes are available to download. Regenerate them first.')
        return redirect('profile')

    site = getattr(settings, 'SITE_NAME', 'BabaengBulacan')
    lines = [
        f"{site} - Two-Factor Backup Recovery Codes",
        "=" * 44,
        "Keep these codes somewhere safe. Each code can be used once.",
        "",
    ] + [f"  {c}" for c in codes] + [
        "",
        f"Generated for: {request.user.email or request.user.username}",
    ]
    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="babaengbulacan-backup-codes.txt"'
    return response


# ===========================================================================
# Contact form (CAPTCHA protected)
# ===========================================================================
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ContactView(View):
    """Contact form with CAPTCHA protection."""

    def get(self, request):
        return render(request, 'pages/contact.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not captcha_passed(request):
            return render(request, 'pages/contact.html', {
                'error': 'reCAPTCHA verification failed. Please try again.',
                'name': name, 'email': email, 'subject': subject, 'message': message,
            })

        if not all([name, email, subject, message]):
            return render(request, 'pages/contact.html', {
                'error': 'Please complete all fields.',
                'name': name, 'email': email, 'subject': subject, 'message': message,
            })

        # Deliver the message to the support inbox (console backend in dev).
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f'[Contact] {subject}',
                message=f'From: {name} <{email}>\n\n{message}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@babaengbulacan.local')],
                fail_silently=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Contact form delivery failed: %s", exc)

        return render(request, 'pages/contact.html', {
            'success': 'Thank you for reaching out. We have received your message and will respond soon.',
        })


def get_captcha_challenge(request):
    """API endpoint to get a new CAPTCHA challenge"""
    try:
        captcha = generate_captcha_challenge()
        if captcha:
            return JsonResponse({
                'success': True,
                'session_id': captcha['session_id'],
                'images': captcha['images'],
                'label': captcha['label'],
                'category': captcha['category']
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to generate CAPTCHA'})
    except Exception as e:
        logger.error(f"Error in get_captcha_challenge: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


class ResourceCenterView(View):
    """Handle Resource Center page (uses free Leaflet.js map)"""
    
    def get(self, request):
        """Render resource center page"""
        # No API key needed - using free Leaflet.js with OpenStreetMap
        context = {}
        return render(request, 'resources/resource_center.html', context)


def home_view(request):
    """Render the public home page."""
    return render(request, 'pages/home.html')


def about_view(request):
    """Render the public about page."""
    return render(request, 'pages/about.html')


def faq_view(request):
    """Render the public FAQ page."""
    return render(request, 'pages/faq.html')


def privacy_view(request):
    """Render the privacy policy page."""
    return render(request, 'pages/privacy.html')


def terms_view(request):
    """Render the terms of service page."""
    return render(request, 'pages/terms.html')


def programs_view(request):
    """Render the public programs page."""
    return render(request, 'programs/program_list.html')


def track_case_view(request):
    """Render the public case tracking page."""
    return render(request, 'reports/track_case.html')


def report_success_view(request):
    """Render the incident report success page."""
    return render(request, 'reports/report_success.html')


class ChatbotPageView(View):
    """Render the chatbot page"""
    
    def get(self, request):
        """Display chatbot page"""
        return render(request, 'chatbot/chat.html')


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    """Handle chatbot API requests"""
    
    def post(self, request):
        """
        Process user message and return chatbot response
        
        Expected POST data:
        {
            "message": "user's question",
            "session_id": "optional session id"
        }
        """
        try:
            # Parse request data
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id', '')
            
            # Validate message
            if not user_message or len(user_message) < 2:
                return JsonResponse({
                    'error': 'Message is too short. Please ask a proper question.',
                    'success': False
                }, status=400)
            
            if len(user_message) > 500:
                return JsonResponse({
                    'error': 'Message is too long. Please keep it under 500 characters.',
                    'success': False
                }, status=400)
            
            # Get chatbot response
            from .chatbot_engine import get_chatbot
            chatbot = get_chatbot()
            response = chatbot.get_answer(user_message)
            
            # Save chat history
            from .models import ChatHistory
            chat_record = ChatHistory.objects.create(
                session_id=session_id or str(uuid.uuid4()),
                user=request.user if request.user.is_authenticated else None,
                user_message=user_message,
                bot_response=response['answer'],
                confidence=response.get('confidence', 0),
                faq_id=response.get('faq_id'),
                intent=response.get('intent', 'general')
            )
            
            return JsonResponse({
                'success': True,
                'message': user_message,
                'response': response['answer'],
                'confidence': float(response.get('confidence', 0)),
                'session_id': chat_record.session_id,
                'intent': response.get('intent', 'general'),
                'faq_id': int(response.get('faq_id')) if response.get('faq_id') else None
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Chatbot API JSON decode error: {str(e)}")
            return JsonResponse({
                'error': 'Invalid JSON format',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Chatbot API error: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'error': 'An error occurred processing your message',
                'success': False
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotHistoryView(View):
    """Get chat history for a session"""
    
    def get(self, request):
        """Retrieve chat history"""
        try:
            session_id = request.GET.get('session_id', '')
            
            if not session_id:
                return JsonResponse({
                    'error': 'Session ID is required',
                    'success': False
                }, status=400)
            
            from .models import ChatHistory
            
            # Get all messages for this session
            messages = ChatHistory.objects.filter(session_id=session_id).values(
                'user_message', 'bot_response', 'created_at', 'confidence'
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'messages': list(messages),
                'total': messages.count()
            })
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return JsonResponse({
                'error': 'Error retrieving chat history',
                'success': False
            }, status=500)


@method_decorator(csrf_protect, name='dispatch')
class IncidentReportView(View):
    """
    Handle incident reporting form submission.
    
    Demonstrates Django concepts:
    - Form rendering (GET request)
    - Form processing and validation (POST request)
    - CSRF protection (automatic with @method_decorator)
    - File uploads
    - Error handling and user feedback
    - Redirect after successful POST
    """
    
    def get(self, request):
        """
        Display the incident report form.
        
        GET request: Render the form template with an empty form
        """
        form = IncidentReportForm()
        context = {
            'form': form,
            'page_title': 'Report an Incident',
        }
        return render(request, 'reports/incident_report.html', context)
    
    def post(self, request):
        """
        Process the submitted incident report form.
        
        POST request: Validate form data, save to database, and redirect
        """
        # CAPTCHA protection against automated/spam submissions
        if not captcha_passed(request):
            messages.error(request, 'reCAPTCHA verification failed. Please try again.')
            return render(request, 'reports/incident_report.html', {
                'form': IncidentReportForm(request.POST, request.FILES),
                'page_title': 'Report an Incident',
            })

        form = IncidentReportForm(request.POST, request.FILES)
        
        # Form validation is automatic via ModelForm
        if form.is_valid():
            try:
                # Save the form to database
                incident = form.save(commit=False)
                
                # Associate with logged-in user if available
                if request.user.is_authenticated:
                    incident.user = request.user
                
                incident.save()
                
                # Success message
                messages.success(
                    request,
                    f'Thank you for reporting this incident. Your report ID is: {incident.report_id}. '
                    f'We will review your report shortly.'
                )
                
                logger.info(
                    f"Incident report submitted - ID: {incident.report_id}, "
                    f"Type: {incident.incident_type}, "
                    f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
                )
                
                # Redirect to success page
                return redirect('report_success')
            
            except Exception as e:
                logger.error(f"Error saving incident report: {str(e)}", exc_info=True)
                messages.error(
                    request,
                    'An error occurred while submitting your report. Please try again.'
                )
                # Return to form with error message
                context = {
                    'form': form,
                    'page_title': 'Report an Incident',
                }
                return render(request, 'reports/incident_report.html', context)
        
        else:
            # Form has validation errors
            # Extract and display error messages
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form[field].label if field != '__all__' else 'Form'
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            
            for error_msg in error_messages:
                messages.error(request, error_msg)
            
            logger.warning(
                f"Invalid incident report form submission. Errors: {form.errors}"
            )
            
            # Return to form with validation errors
            context = {
                'form': form,
                'page_title': 'Report an Incident',
            }
            return render(request, 'reports/incident_report.html', context)


def incident_report_view(request):
    """
    Function-based view wrapper for incident reporting.
    Demonstrates both GET and POST handling in a single function.
    """
    view = IncidentReportView()
    view.request = request
    
    if request.method == 'GET':
        return view.get(request)
    elif request.method == 'POST':
        return view.post(request)
    else:
        return redirect('incident_report')
