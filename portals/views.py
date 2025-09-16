from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Teacher, TeacherAssignment
from .serializers import TeacherSerializer, TeacherAssignmentSerializer
# Create your views here.

class IsAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Teacher.objects.select_related("user").all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdminOrSelf]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        t = Teacher.objects.select_related("user").filter(user=request.user).first()
        if not t:
            return Response(None)
        return Response(self.get_serializer(t).data)

class TeacherAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeacherAssignment.objects.select_related(
        "teacher__user","class_subject__classroom__level","class_subject__classroom__year","class_subject__subject"
    ).all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrSelf]

    @action(detail=False, methods=["get"], url_path="my")
    def my(self, request):
        qs = self.get_queryset().filter(teacher__user=request.user)
        return Response(self.get_serializer(qs, many=True).data)