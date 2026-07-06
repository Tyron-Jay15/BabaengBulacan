from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from .models import UserProfile


class SessionTimeoutMiddleware:
    """
    Middleware to check session timeout for authenticated users
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.is_session_expired():
                    was_staff = request.user.is_staff or request.user.is_superuser
                    from django.contrib.auth import logout
                    logout(request)
                    login_name = 'admin_login' if was_staff else 'login'
                    return redirect(reverse(login_name) + '?message=Your session has expired. Please login again.')
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = UserProfile.objects.create(user=request.user)
        
        response = self.get_response(request)
        return response