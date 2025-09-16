from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AssessmentType, Assessment, Score
from .serializers import (
    AssessmentTypeSerializer, AssessmentSerializer, ScoreSerializer,
    BulkAssessmentCreateSerializer, BulkScoresUpsertSerializer
)
from .permissions import IsTeacherOrAdminWrite

class AssessmentTypeViewSet(viewsets.ModelViewSet):
    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer
    permission_classes = [IsTeacherOrAdminWrite]

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related("term","class_subject","atype").all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsTeacherOrAdminWrite]

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create_assessments(self, request):
        ser = BulkAssessmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_201_CREATED)

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.select_related("assessment","enrollment_subject").all()
    serializer_class = ScoreSerializer
    permission_classes = [IsTeacherOrAdminWrite]

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_upsert(self, request):
        ser = BulkScoresUpsertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)
