from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, ClassSubjectViewSet

router = DefaultRouter()
router.register(r"subjects/subjects", SubjectViewSet, basename="subjects")
router.register(r"subjects/class-subjects", ClassSubjectViewSet, basename="class-subjects")
urlpatterns = router.urls
