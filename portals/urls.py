# portals/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import TeacherViewSet, TeacherAssignmentViewSet, TeacherFullCreateView

router = DefaultRouter()
router.register(r"portal/teachers", TeacherViewSet, basename="portal-teachers")
router.register(r"portal/assignments", TeacherAssignmentViewSet, basename="portal-assignments")
urlpatterns = router.urls

urlpatterns = [
    path("", include(router.urls)),
    path("api/portal/teachers/full-create/", TeacherFullCreateView.as_view(), name="portal-teachers-full-create"),
]
