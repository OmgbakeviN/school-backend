from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Term
from subjects.models import ClassSubject
from enrollments.models import EnrollmentSubject

# Create your models here.

class AssessmentType(models.Model):
    code = models.CharField(max_length=8, unique=True)  # ex: CA1, CA2
    name = models.CharField(max_length=32, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=50.00,
                                 validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.weight}%)"

class Assessment(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="assessments")
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name="assessments")
    atype = models.ForeignKey(AssessmentType, on_delete=models.PROTECT, related_name="assessments")

    class Meta:
        unique_together = (("term", "class_subject", "atype"),)
        ordering = ["term__year__name", "term__index", "class_subject__classroom__name", "class_subject__subject__name", "atype__code"]

    def __str__(self):
        return f"{self.term} | {self.class_subject} | {self.atype.code}"

class Score(models.Model):
    enrollment_subject = models.ForeignKey(EnrollmentSubject, on_delete=models.CASCADE, related_name="scores")
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="scores")
    value = models.DecimalField(max_digits=5, decimal_places=2,
                                validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        unique_together = (("enrollment_subject", "assessment"),)
        ordering = ["assessment", "enrollment_subject"]

    def __str__(self):
        return f"{self.enrollment_subject} → {self.assessment}: {self.value}"