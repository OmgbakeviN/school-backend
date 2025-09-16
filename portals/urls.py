# portals/urls.py
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, TeacherAssignmentViewSet

router = DefaultRouter()
router.register(r"portal/teachers", TeacherViewSet, basename="portal-teachers")
router.register(r"portal/assignments", TeacherAssignmentViewSet, basename="portal-assignments")
urlpatterns = router.urls
