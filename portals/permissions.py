from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsRegistrarOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # adapte selon ton modèle d’utilisateurs
        return request.user and request.user.is_authenticated and getattr(request.user, "role", None) in ("REGISTRAR", "ADMIN")
