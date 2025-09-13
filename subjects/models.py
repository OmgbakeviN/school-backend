from django.db import models
from django.core.validators import MinValueValidator
from core.models import Classroom

# Create your models here.

class Subject(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.code}]"

class ClassSubject(models.Model):
    classroom   = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="class_subjects")
    subject     = models.ForeignKey(Subject,   on_delete=models.PROTECT, related_name="class_subjects")
    coefficient = models.DecimalField(max_digits=5, decimal_places=2, default=1, validators=[MinValueValidator(0.01)])
    is_core     = models.BooleanField(default=False)

    class Meta:
        unique_together = (("classroom", "subject"),)
        ordering = ["classroom", "subject__name"]

    def __str__(self):
        return f"{self.classroom} - {self.subject} (coef {self.coefficient})"