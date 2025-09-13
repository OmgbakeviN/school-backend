from django.contrib import admin
from .models import Student, Enrollment, EnrollmentSubject
# Register your models here.

class EnrollmentSubjectInline(admin.TabularInline):
    model = EnrollmentSubject
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matricule","last_name","first_name","sex","dob","house")
    search_fields = ("matricule","last_name","first_name")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student","classroom","active","date_enrolled")
    list_filter = ("classroom__year","classroom__level","classroom__stream","active")
    search_fields = ("student__matricule","student__last_name","student__first_name","classroom__name")
    inlines = [EnrollmentSubjectInline]

@admin.register(EnrollmentSubject)
class EnrollmentSubjectAdmin(admin.ModelAdmin):
    list_display = ("enrollment","class_subject","coef_override","selected")
    list_filter = ("enrollment__classroom__year","enrollment__classroom__level","enrollment__classroom__stream","selected")
    search_fields = ("enrollment__student__matricule","class_subject__subject__name","class_subject__subject__code")