from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Student, Enrollment, EnrollmentSubject
from .serializers import StudentSerializer, EnrollmentSerializer, EnrollmentSubjectSerializer, EnrollmentSubjectDetailSerializer

# Create your views here.

class IsAuthenticatedRW(permissions.IsAuthenticated):
    pass

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedRW]
    filterset_fields = []
    search_fields = ["matricule","last_name","first_name"]

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related("student", "classroom").all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def subjects(self, request, pk=None):
        # get_object() => 404 si inexistant + applique les permissions objet
        enrollment = self.get_object()
        qs = (
            EnrollmentSubject.objects
            .filter(enrollment=enrollment, selected=True)             # <-- Option A strict
            .select_related("class_subject__subject")
            .order_by("class_subject__subject__name")                 # <-- ordre lisible
        )
        return Response(EnrollmentSubjectDetailSerializer(qs, many=True).data)

    

class EnrollmentSubjectViewSet(viewsets.ModelViewSet):
    queryset = EnrollmentSubject.objects.select_related("enrollment","class_subject").all()
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