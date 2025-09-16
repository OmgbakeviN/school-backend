from django.db import models
from core.models import AcademicYear
# Create your models here.

class GradeScale(models.Model):
    name = models.CharField(max_length=32)
    year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="grade_scales")

    class Meta:
        unique_together = (("name", "year"),)
        ordering = ["year__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.year.name})"

class GradeBand(models.Model):
    scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name="bands")
    letter = models.CharField(max_length=2)  # A, B, C, ...
    min_mark = models.PositiveSmallIntegerField()  # inclusif
    max_mark = models.PositiveSmallIntegerField()  # inclusif
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    class Meta:
        unique_together = (("scale", "letter"),)
        ordering = ["-min_mark"]

    def __str__(self):
        return f"{self.letter}: {self.min_mark}-{self.max_mark}"

