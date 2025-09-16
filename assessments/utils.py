# assessments/utils.py
from portals.models import TeacherAssignment

def teacher_can_edit(user, class_subject_id: int) -> bool:
    role = getattr(user, "role", None)
    if role in ("ADMIN","REGISTRAR","PRINCIPAL"):
        return True
    if role != "TEACHER":
        return False
    return TeacherAssignment.objects.filter(
        teacher__user=user, class_subject_id=class_subject_id, can_edit=True
    ).exists()
