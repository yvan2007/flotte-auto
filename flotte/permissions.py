"""Permissions REST Framework — rôles FLOTTE (manager, admin)."""
from rest_framework import permissions
from .mixins import is_manager_or_admin


class IsManagerOrAdmin(permissions.BasePermission):
    """Autorise uniquement les utilisateurs avec rôle manager ou admin."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return is_manager_or_admin(request)
