from django.contrib import admin
from .models import AssessmentType, Assessment, Score
# Register your models here.

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "weight", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("term", "class_subject", "atype")
    list_filter = ("term__year", "term__index", "class_subject__classroom__level", "class_subject__classroom__stream", "atype__code")
    search_fields = ("class_subject__classroom__name", "class_subject__subject__name", "atype__code")

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("assessment", "enrollment_subject", "value")
    list_filter = ("assessment__term__year", "assessment__term__index", "assessment__class_subject__classroom__level")
    search_fields = ("enrollment_subject__enrollment__student__matricule", "assessment__class_subject__subject__name")