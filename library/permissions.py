from rest_framework.permissions import BasePermission, SAFE_METHODS

class StudentPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(
                name__iexact="student"
            ).exists()
        )

class MasterDataPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in SAFE_METHODS
            or request.user.groups.filter(name__iexact="admin").exists()
            or request.user.is_superuser
        )
