from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTeacherOrAdminWrite(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # écriture réservée aux TEACHER / ADMIN (placeholder)
        user = request.user
        role = getattr(user, "role", None)
        return user and user.is_authenticated and role in ("TEACHER", "ADMIN")