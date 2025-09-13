from django.contrib import admin
from .models import Subject, ClassSubject
# Register your models here.

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "short_name")
    search_fields = ("code", "name", "short_name")

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("classroom", "subject", "coefficient", "is_core")
    list_filter  = ("classroom__year", "classroom__level", "classroom__stream", "is_core")
    search_fields = ("classroom__name", "subject__name", "subject__code")