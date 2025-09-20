# assessments/utils.py
from portals.models import TeacherAssignment

ALLOWED_WRITE_ROLES = {"ADMIN", "REGISTRAR", "PRINCIPAL"}

def teacher_can_edit(user, class_subject_id: int) -> bool:
    """
    True si:
      - user est ADMIN/REGISTRAR/PRINCIPAL (écriture autorisée), ou
      - user est TEACHER ET assigné à class_subject_id avec can_edit=True.
    """
    if not getattr(user, "is_authenticated", False):
        return False

    role = getattr(user, "role", None)
    if role in ALLOWED_WRITE_ROLES:
        return True

    if role != "TEACHER":
        return False

    # lier User -> Teacher via OneToOne (user.teacher)
    teacher = getattr(user, "teacher", None)
    if not teacher:
        return False

    return TeacherAssignment.objects.filter(
        teacher=teacher,
        class_subject_id=class_subject_id,
        can_edit=True,
    ).exists()
