from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import AcademicYear, Term, Level, Stream, Classroom
from .serializers import (
    AcademicYearSerializer, TermSerializer, LevelSerializer, StreamSerializer, ClassroomSerializer
)
# Create your views here.

class IsRegistrarOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated): return False
        return getattr(user, "role", None) in ("REGISTRAR","ADMIN","PRINCIPAL") or request.method in ("GET",)

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]

    @action(detail=True, methods=["post"])
    def seed_terms(self, request, pk=None):
        """Crée Term 1..3 pour l'année si absents"""
        year = self.get_object()
        created = []
        for i in (1,2,3):
            obj, ok = Term.objects.get_or_create(year=year, index=i)
            if ok: created.append(obj.id)
        return Response({"created": created})

class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.select_related("year").all()
    serializer_class = TermSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year","index"]

class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [permissions.IsAuthenticated]

class StreamViewSet(viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_active"]

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.select_related("year","level","stream").all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year","level","stream","name"]


