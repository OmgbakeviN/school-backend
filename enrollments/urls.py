from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, EnrollmentViewSet, EnrollmentSubjectViewSet

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="students")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollments")
router.register(r"enrollment-subjects", EnrollmentSubjectViewSet, basename="enrollment-subjects")
urlpatterns = router.urls
