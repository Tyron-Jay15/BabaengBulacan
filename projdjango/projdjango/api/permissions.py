"""
Custom DRF permission classes for BabaengBulacan APIs.

Keeps read access open for GET (browser/Postman demos) while restricting
writes to authenticated users or staff as appropriate.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated, IsAdminUser


class IsStaffOrReadOnly(BasePermission):
    """Allow anyone to read; only staff can create/update/delete."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    """Allow anyone to read; only admin users can write (e.g. user management)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrStaff(BasePermission):
    """Object-level: owner or staff can access notifications."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return getattr(obj, 'user', None) == request.user
