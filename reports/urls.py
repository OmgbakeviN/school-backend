from django.urls import path
from .views import StudentTermPreviewView, ClassTermPreviewView, StudentPDFView, ClassPDFBatchView, ReportVerifyPage

urlpatterns = [
    path("reports/preview/student", StudentTermPreviewView.as_view()),
    path("reports/preview/class",   ClassTermPreviewView.as_view()),
    path("api/reports/pdf/student/", StudentPDFView.as_view(), name="report-pdf-student"),
    path("api/reports/pdf/class/", ClassPDFBatchView.as_view(), name="report-pdf-class"),
    path("reports/verify/<uuid:uid>/", ReportVerifyPage.as_view(), name="report-verify")
]
