from rest_framework.routers import DefaultRouter
from .views import AcademicYearViewSet, TermViewSet, LevelViewSet, StreamViewSet, ClassroomViewSet

router = DefaultRouter()
router.register(r"core/years", AcademicYearViewSet, basename="years")
router.register(r"core/terms", TermViewSet, basename="terms")
router.register(r"core/levels", LevelViewSet, basename="levels")
router.register(r"core/streams", StreamViewSet, basename="streams")
router.register(r"core/classes", ClassroomViewSet, basename="classes")
urlpatterns = router.urls
