from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Subject, ClassSubject
from .serializers import SubjectSerializer, ClassSubjectSerializer, ClassSubjectDetailSerializer

class IsRegistrarOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated): return False
        return getattr(user, "role", None) in ("REGISTRAR","ADMIN","PRINCIPAL") or request.method in ("GET",)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    search_fields = ["code","name","short_name"]

class ClassSubjectViewSet(viewsets.ModelViewSet):
    queryset = ClassSubject.objects.select_related("classroom","subject").all()
    serializer_class = ClassSubjectSerializer
    permission_classes = [IsRegistrarOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["classroom","subject","classroom__year","classroom__level","classroom__stream"]

    @action(detail=False, methods=["get"], url_path="by-class")
    def by_class(self, request):
        classroom_id = request.query_params.get("classroom")
        if not classroom_id:
            return Response({"detail":"classroom is required"}, status=400)
        qs = self.get_queryset().filter(classroom_id=classroom_id).order_by("subject__name")
        return Response(ClassSubjectDetailSerializer(qs, many=True).data)
