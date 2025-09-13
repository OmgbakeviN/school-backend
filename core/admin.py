from django.contrib import admin
from .models import AcademicYear, Term, Level, Stream, Classroom
from subjects.models import Subject, ClassSubject
# Register your models here.
class ClassSubjectInline(admin.TabularInline):
    model = ClassSubject
    extra = 1

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name",)

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("year", "index")
    list_filter  = ("year", "index")
    search_fields = ("year__name",)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    list_filter  = ("code",)
    search_fields = ("code", "name")

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter  = ("is_active",)
    search_fields = ("name",)

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "level", "stream")
    list_filter  = ("year", "level", "stream")
    search_fields = ("name",)
    inlines = [ClassSubjectInline]