from django.urls import path
from .views import StudentTermPreviewView, ClassTermPreviewView

urlpatterns = [
    path("reports/preview/student", StudentTermPreviewView.as_view()),
    path("reports/preview/class",   ClassTermPreviewView.as_view()),
]
