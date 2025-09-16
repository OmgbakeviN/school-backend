from django.contrib import admin
from .models import ReportToken
# Register your models here.

@admin.register(ReportToken)
class ReportTokenAdmin(admin.ModelAdmin):
    list_display = ("uid","enrollment","term","created_at","valid")
    list_filter = ("valid","term__year","term__index")
    search_fields = ("enrollment__student__matricule","enrollment__student__last_name","enrollment__student__first_name")

