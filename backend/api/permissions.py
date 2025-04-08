from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminAuthorOrReadOnly(BasePermission):
    """Права доступа для автора или администратора."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_admin
            or obj.author == request.user)
