from rest_framework.routers import DefaultRouter
from .views import AssessmentTypeViewSet, AssessmentViewSet, ScoreViewSet

router = DefaultRouter()  # trailing slash par défaut
router.register(r"assessment-types", AssessmentTypeViewSet, basename="assessment-types")
router.register(r"assessments", AssessmentViewSet, basename="assessments")
router.register(r"scores", ScoreViewSet, basename="scores")
urlpatterns = router.urls
