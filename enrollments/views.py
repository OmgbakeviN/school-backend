# enrollments/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Student, Enrollment, EnrollmentSubject
from .serializers import (
    StudentSerializer, EnrollmentSerializer, EnrollmentSubjectSerializer,
    EnrollmentDetailSerializer
)

class IsAuthenticatedRW(permissions.IsAuthenticated):
    pass

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["matricule","last_name","first_name"]

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related(
        "student","classroom__year","classroom__level"
    ).all()
    permission_classes = [IsAuthenticatedRW]
    serializer_class = EnrollmentSerializer

    def get_serializer_class(self):
        # list/retrieve → serializer enrichi (noms, classe, niveau, année)
        if self.action in ("list","retrieve"):
            return EnrollmentDetailSerializer
        return EnrollmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        classroom = self.request.query_params.get("classroom")
        student = self.request.query_params.get("student")
        year = self.request.query_params.get("year")
        if classroom:
            qs = qs.filter(classroom_id=classroom)
        if student:
            qs = qs.filter(student_id=student)
        if year:
            # autorise filtra par id d'année OU par libellé "2025/2026"
            if year.isdigit():
                qs = qs.filter(classroom__year_id=int(year))
            else:
                qs = qs.filter(classroom__year__name=year)
        return qs

    @action(detail=True, methods=["get"])
    def subjects(self, request, pk=None):
        enrollment = self.get_object()
        es = (EnrollmentSubject.objects
              .filter(enrollment=enrollment, selected=True)
              .select_related("class_subject__subject")
              .order_by("class_subject__subject__name"))
        from .serializers import EnrollmentSubjectDetailSerializer  # évite import circulaire
        return Response(EnrollmentSubjectDetailSerializer(es, many=True).data)

class EnrollmentSubjectViewSet(viewsets.ModelViewSet):
    queryset = EnrollmentSubject.objects.select_related(
        "enrollment__student","enrollment__classroom","class_subject__subject"
    ).all()
    serializer_class = EnrollmentSubjectSerializer
    permission_classes = [IsAuthenticatedRW]

    def get_queryset(self):
        qs = super().get_queryset()
        enrollment = self.request.query_params.get("enrollment")
        classroom = self.request.query_params.get("classroom")
        if enrollment:
            qs = qs.filter(enrollment_id=enrollment)
        if classroom:
            qs = qs.filter(enrollment__classroom_id=classroom)
        return qs
