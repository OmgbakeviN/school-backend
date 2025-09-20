# portals/serializers.py
from rest_framework import serializers
from .models import Teacher, TeacherAssignment
from django.contrib.auth import get_user_model
from subjects.models import ClassSubject

User = get_user_model()

class TeacherSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = Teacher
        fields = ["id","username","full_name","staff_code","email",]
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class_subject_id = serializers.IntegerField(source="class_subject.id", read_only=True)
    classroom_id = serializers.IntegerField(source="class_subject.classroom.id", read_only=True)
    classroom_name = serializers.CharField(source="class_subject.classroom.name", read_only=True)
    subject_id = serializers.IntegerField(source="class_subject.subject.id", read_only=True)
    subject_code = serializers.CharField(source="class_subject.subject.code", read_only=True)
    subject_name = serializers.CharField(source="class_subject.subject.name", read_only=True)
    class Meta:
        model = TeacherAssignment
        fields = ["id","can_edit","class_subject_id","classroom_id","classroom_name","subject_id","subject_code","subject_name"]

# Ecriture Teacher : on choisit un user existant (id) + staff_code
class TeacherWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Teacher
        fields = ["id", "user", "staff_code"]

# Ecriture Assignment : ids directs
class TeacherAssignmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAssignment
        fields = ["id", "teacher", "class_subject", "can_edit"]

    def validate(self, attrs):
        # évite d'affecter un class_subject à une autre classe par erreur si besoin
        return attrs