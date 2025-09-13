from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class AcademicYear(models.Model):
    """
    Exemple de nom: '2025/2026'
    """
    name = models.CharField(max_length=9, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name

class Term(models.Model):
    year  = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="terms")
    index = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])  # 1..3

    class Meta:
        unique_together = (("year", "index"),)
        ordering = ["year", "index"]

    def __str__(self):
        return f"{self.year.name} - Term {self.index}"

class Level(models.Model):
    class Code(models.TextChoices):
        F1 = "F1", "Form 1"
        F2 = "F2", "Form 2"
        F3 = "F3", "Form 3"
        F4 = "F4", "Form 4"
        F5 = "F5", "Form 5"
        L6 = "L6", "Lower Sixth"
        U6 = "U6", "Upper Sixth"

    code = models.CharField(max_length=8, unique=True, choices=Code.choices)
    name = models.CharField(max_length=32)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name

class Stream(models.Model):
    """
    Filière (principalement pour F4-F5-L6-U6)
    """
    name = models.CharField(max_length=32, unique=True)  # 'Science', 'Arts'
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Classroom(models.Model):
    year   = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="classes")
    level  = models.ForeignKey(Level,        on_delete=models.PROTECT, related_name="classes")
    stream = models.ForeignKey(Stream,       on_delete=models.PROTECT, null=True, blank=True, related_name="classes")
    name   = models.CharField(max_length=32)  # 'Form 5A', 'L6 Sci', etc.

    class Meta:
        unique_together = (("year", "name"),)
        ordering = ["year", "level__code", "name"]

    def __str__(self):
        return f"{self.name} ({self.year})"

