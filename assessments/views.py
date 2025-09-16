# assessments/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action    # <-- IMPORT INDISPENSABLE
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import AssessmentType, Assessment, Score
from .serializers import (
    AssessmentTypeSerializer, AssessmentSerializer, ScoreSerializer,
    BulkAssessmentCreateSerializer, BulkScoresUpsertSerializer
)
from .permissions import IsTeacherOrAdminWrite
from .utils import teacher_can_edit
from subjects.models import ClassSubject

class AssessmentTypeViewSet(viewsets.ModelViewSet):
    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer
    permission_classes = [IsTeacherOrAdminWrite]

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related(
        "term","class_subject__classroom","class_subject__subject","atype"
    )
    serializer_class = AssessmentSerializer
    permission_classes = [IsTeacherOrAdminWrite]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["term","class_subject","atype"]

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create_assessments(self, request):
        # Si TEACHER: vérifier l’assignation pour chaque class_subject
        if getattr(request.user, "role", None) == "TEACHER":
            body = request.data or {}
            if "class_subjects" in body:
                cs_ids = list(body["class_subjects"])
            elif "classroom" in body:
                cs_ids = list(ClassSubject.objects.filter(
                    classroom_id=body["classroom"]
                ).values_list("id", flat=True))
            else:
                cs_ids = []
            for cs_id in cs_ids:
                if not teacher_can_edit(request.user, cs_id):
                    raise PermissionDenied("Not allowed to create assessments for this subject/class.")
        ser = BulkAssessmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.save()
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="scores")
    def scores(self, request, pk=None):
        """Liste des scores pour cette épreuve (id = pk)."""
        assessment = self.get_object()
        qs = Score.objects.filter(assessment=assessment).select_related("enrollment_subject__enrollment__student")
        data = [
            {
                "id": s.id,
                "enrollment_subject": s.enrollment_subject_id,
                "student": {
                    "id": s.enrollment_subject.enrollment.student.id,
                    "matricule": s.enrollment_subject.enrollment.student.matricule,
                    "name": f"{s.enrollment_subject.enrollment.student.last_name} {s.enrollment_subject.enrollment.student.first_name}",
                },
                "value": float(s.value),
            }
            for s in qs
        ]
        return Response(data)

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.select_related(
        "assessment__atype","assessment__class_subject__classroom","enrollment_subject"
    )
    serializer_class = ScoreSerializer
    permission_classes = [IsTeacherOrAdminWrite]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["assessment"]  # GET /api/scores/?assessment=<id>

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request, *args, **kwargs):
        """Upsert de notes pour un assessment (CA1/CA2)."""
        ser = BulkScoresUpsertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assessment = ser.validated_data["assessment_obj"]

        if getattr(request.user, "role", None) == "TEACHER":
            cs_id = assessment.class_subject_id
            if not teacher_can_edit(request.user, cs_id):
                raise PermissionDenied("Not allowed to edit scores for this subject/class.")

        result = ser.save()
        return Response(result, status=status.HTTP_200_OK)
