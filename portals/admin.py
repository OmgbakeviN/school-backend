from django.contrib import admin
from .models import Teacher, TeacherAssignment
# Register your models here.

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "staff_code")

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher","class_subject","can_edit")
    list_filter = ("can_edit","class_subject__classroom__year","class_subject__classroom__level")
    search_fields = ("teacher__user__username","class_subject__subject__name","class_subject__classroom__name")