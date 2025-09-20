from rest_framework import viewsets, permissions, status 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Teacher, TeacherAssignment
from .serializers import (
    TeacherSerializer, TeacherWriteSerializer,
    TeacherAssignmentSerializer, TeacherAssignmentWriteSerializer
)
from .permissions import IsRegistrarOrAdmin
from subjects.models import ClassSubject
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

# --- TEACHERS ---
class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related("user").all()
    permission_classes = [IsAdminOrSelf]  # lecture pour tous connectés
    # écriture restreinte via get_permissions()

    def get_permissions(self):
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [IsRegistrarOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return TeacherWriteSerializer
        return TeacherSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        t = Teacher.objects.select_related("user").filter(user=request.user).first()
        if not t:
            return Response(None)
        return Response(TeacherSerializer(t).data)

# --- ASSIGNMENTS ---
class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeacherAssignment.objects.select_related(
        "teacher__user", "class_subject__classroom__level",
        "class_subject__classroom__year", "class_subject__subject"
    ).all()
    permission_classes = [IsAdminOrSelf]

    def get_permissions(self):
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [IsRegistrarOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return TeacherAssignmentWriteSerializer
        return TeacherAssignmentSerializer

    @action(detail=False, methods=["get"], url_path="my")
    def my(self, request):
        qs = self.get_queryset().filter(teacher__user=request.user)
        return Response(TeacherAssignmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="by-classroom")
    def by_classroom(self, request):
        """
        GET /api/portal/assignments/by-classroom?classroom=<id>
        → liste des assignments (utile pour l’UI Registrar)
        """
        classroom = request.GET.get("classroom")
        qs = self.get_queryset()
        if classroom:
            qs = qs.filter(class_subject__classroom_id=classroom)
        return Response(TeacherAssignmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="bulk-set-for-class")
    @transaction.atomic
    def bulk_set_for_class(self, request):
        """
        Body:
        {
          "classroom": 12,
          "map": [
             {"class_subject": 55, "teacher": 3, "can_edit": true},
             {"class_subject": 56, "teacher": 4, "can_edit": false}
          ]
        }
        -> upsert des affectations pour cette classe
        """
        classroom = request.data.get("classroom")
        mapping = request.data.get("map", [])
        if not classroom:
            return Response({"detail": "classroom required"}, status=400)

        cs_ids = set(ClassSubject.objects.filter(classroom_id=classroom).values_list("id", flat=True))
        created, updated, skipped = [], [], []
        for item in mapping:
            cs = item.get("class_subject")
            teacher = item.get("teacher")
            can_edit = bool(item.get("can_edit", True))
            if cs not in cs_ids or not teacher:
                skipped.append(item); continue
            obj, was_created = TeacherAssignment.objects.update_or_create(
                class_subject_id=cs, defaults={"teacher_id": teacher, "can_edit": can_edit}
            )
            (created if was_created else updated).append(obj.id)
        return Response({"created": created, "updated": updated, "skipped": skipped})

class TeacherFullCreateView(APIView):
    """
    POST /api/portal/teachers/full-create/

    payload:
    {
      "user": {
        "username": "jdoe",
        "password": "P@ssw0rd!",
        "first_name": "John",
        "last_name": "Doe",
        "email": "jd@example.com"
      },
      "staff_code": "T-0042",
      "assignments": [
         {"class_subject": 55, "can_edit": true},
         {"class_subject": 61, "can_edit": true}
      ]
    }
    """
    permission_classes = [IsAuthenticated, IsRegistrarOrAdmin]

    @transaction.atomic
    def post(self, request):
        body = request.data or {}
        udata = body.get("user") or {}
        username = (udata.get("username") or "").strip()
        password = udata.get("password") or ""
        first_name = udata.get("first_name") or ""
        last_name = udata.get("last_name") or ""
        email = udata.get("email") or ""
        staff_code = (body.get("staff_code") or "").strip()
        assignments = body.get("assignments") or []

        if not username or not password:
            return Response({"detail": "username and password are required"}, status=400)

        # 1) créer l'utilisateur + rôle TEACHER
        if User.objects.filter(username=username).exists():
            return Response({"detail": "username already exists"}, status=400)

        user = User(username=username, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        # si ton modèle User a un champ 'role'
        if hasattr(user, "role"):
            user.role = "TEACHER"
        user.save()

        # 2) créer Teacher
        teacher = Teacher.objects.create(user=user, staff_code=staff_code)

        # 3) affectations
        created, skipped = [], []
        # sécuriser que tous les class_subject existent
        cs_ids = set(ClassSubject.objects.filter(
            id__in=[a.get("class_subject") for a in assignments if a.get("class_subject")]
        ).values_list("id", flat=True))

        for a in assignments:
            cs = a.get("class_subject")
            if cs not in cs_ids:
                skipped.append({"class_subject": cs, "reason": "invalid class_subject"})
                continue
            can_edit = bool(a.get("can_edit", True))
            ta, _ = TeacherAssignment.objects.update_or_create(
                teacher=teacher, class_subject_id=cs, defaults={"can_edit": can_edit}
            )
            created.append(ta.id)

        return Response({
            "teacher": {
                "id": teacher.id,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": getattr(user, "role", None),
                },
                "staff_code": teacher.staff_code
            },
            "assignments_created": created,
            "assignments_skipped": skipped
        }, status=status.HTTP_201_CREATED)