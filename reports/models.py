import uuid
from django.db import models
from django.conf import settings
from core.models import Term
from enrollments.models import Enrollment

# Create your models here.
class ReportToken(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="report_tokens")
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField(default=True)
    # Snapshot JSON (facultatif mais utile pour l’archivage)
    payload = models.JSONField(default=dict, blank=True)
    pdf_sha1 = models.CharField(max_length=64, blank=True)

    def __str__(self):
        s = self.enrollment.student
        return f"{self.uid} - {s.matricule} - Term {self.term.index}"

class AnnualReportToken(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="annual_tokens")
    year_label = models.CharField(max_length=64)          # ex: "2025/2026"
    created_at = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField(default=True)
    payload = models.JSONField(default=dict, blank=True)  # snapshot
    pdf_sha1 = models.CharField(max_length=64, blank=True)

    def __str__(self):
        s = self.enrollment.student
        return f"{self.uid} - {s.matricule} - {self.year_label}"