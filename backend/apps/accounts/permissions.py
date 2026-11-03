"""
Role-Based Access Control (RBAC) Permissions conforming to ISO 27001 A.8.3.
"""
from rest_framework import permissions
from apps.accounts.models import UserCredential

class IsSellerOrAdmin(permissions.BasePermission):
    """Allows write/create operations only to Sellers and Administrators."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not (request.user and request.user.is_authenticated):
            return False
        # Verificación directa sobre credencial o catálogo RBAC en UserProfile
        if request.user.role in (UserCredential.ROLE_SELLER, UserCredential.ROLE_ADMIN):
            return True
        profile = getattr(request.user, 'user_profile', None)
        if profile and (profile.has_role('SELLER') or profile.has_role('ADMIN')):
            return True
        return False


class IsAccountOwnerOrReadOnly(permissions.BasePermission):
    """Allows object modifications only if the user owns the corresponding AccountProxy."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == UserCredential.ROLE_ADMIN:
            return True
        # Check if obj.seller_profile matches the UserProfile of request.user
        seller_profile = getattr(obj, 'seller_profile', getattr(obj, 'seller_account', None))
        return bool(seller_profile and seller_profile.user_id == request.user.id)
