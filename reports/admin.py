from django.contrib import admin
from .models import ReportToken, AnnualReportToken
# Register your models here.

@admin.register(ReportToken)
class ReportTokenAdmin(admin.ModelAdmin):
    list_display = ("uid","enrollment","term","created_at","valid")
    list_filter = ("valid","term__year","term__index")
    search_fields = ("enrollment__student__matricule","enrollment__student__last_name","enrollment__student__first_name")

@admin.register(AnnualReportToken)
class AnnualReportTokenAdmin(admin.ModelAdmin):
    list_display = ("uid","enrollment","year_label","created_at","valid")
    list_filter  = ("valid",)
    search_fields = ("enrollment__student__matricule","enrollment__student__last_name","enrollment__student__first_name")