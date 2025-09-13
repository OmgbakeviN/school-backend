from django.db import models
from django.core.validators import MinValueValidator
from core.models import Classroom
from subjects.models import ClassSubject
# Create your models here.

class Student(models.Model):
    MAT_CHOICES = (("M","M"),("F","F"))
    matricule = models.CharField(max_length=32, unique=True)
    last_name = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    sex = models.CharField(max_length=1, choices=MAT_CHOICES)
    dob = models.DateField(null=True, blank=True)
    house = models.CharField(max_length=64, blank=True)
    photo_url = models.URLField(blank=True)

    class Meta:
        ordering = ["last_name","first_name"]

    def __str__(self):
        return f"{self.matricule} - {self.last_name} {self.first_name}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name="enrollments")
    date_enrolled = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("student","classroom"),)
        ordering = ["classroom","student__last_name","student__first_name"]

    def __str__(self):
        return f"{self.student} @ {self.classroom}"

class EnrollmentSubject(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="subjects")
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.PROTECT, related_name="enrollment_links")
    coef_override = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    selected = models.BooleanField(default=True)

    class Meta:
        unique_together = (("enrollment","class_subject"),)
        ordering = ["enrollment","class_subject__subject__name"]

    def __str__(self):
        return f"{self.enrollment} → {self.class_subject}"