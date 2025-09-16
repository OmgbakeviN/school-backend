from django.urls import path
from .views import class_stats

urlpatterns = [
    path("analytics/classes/<int:classroom_id>/stats/", class_stats),
]
