# assessments/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

READONLY_ROLES = {"TEACHER", "REGISTRAR", "PRINCIPAL", "ADMIN"}
WRITE_ROLES    = {"TEACHER", "REGISTRAR", "PRINCIPAL", "ADMIN"}

class IsTeacherOrAdminWrite(BasePermission):
    """
    - Lecture: tout utilisateur authentifié (avec un rôle prévu)
    - Écriture: TEACHER/REGISTRAR/PRINCIPAL/ADMIN
      (NB: pour les TEACHER, le périmètre réel d'édition est
       re-vérifié par teacher_can_edit(...) dans la vue.)
    """
    def has_permission(self, request, view):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False

        role = getattr(user, "role", None)

        # GET/HEAD/OPTIONS -> lecture
        if request.method in SAFE_METHODS:
            return role in READONLY_ROLES

        # POST/PUT/PATCH/DELETE -> écriture
        return role in WRITE_ROLES
