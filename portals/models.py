from django.db import models
from django.conf import settings
from subjects.models import ClassSubject
# Create your models here.

User = settings.AUTH_USER_MODEL

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher")
    staff_code = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="assignments")
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name="teacher_assignments")
    can_edit = models.BooleanField(default=True)

    class Meta:
        unique_together = (("teacher","class_subject"),)

    def __str__(self):
        cs = self.class_subject
        return f"{self.teacher} → {cs.classroom.name} / {cs.subject.name} ({'edit' if self.can_edit else 'read'})"

