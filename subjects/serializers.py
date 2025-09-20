from rest_framework import serializers
from .models import Subject, ClassSubject

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id","code","name","short_name"]

class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "code", "name"]

class ClassSubjectSerializer(serializers.ModelSerializer):
    # champs plats lisibles
    subject_id = serializers.IntegerField(source="subject.id", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    # (option) renvoyer aussi l’objet complet si tu préfères
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)

    class Meta:
        model = ClassSubject
        fields = [
            "id",
            "classroom", "classroom_name",
            "subject", "subject_id", "subject_code", "subject_name", "subject_detail",
            "coefficient", "is_core",
        ]

# Détail pour UI (avec infos matière)
class ClassSubjectDetailSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(source="subject.id", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    class Meta:
        model = ClassSubject
        fields = ["id","classroom","subject","coefficient","is_core","subject_id","subject_code","subject_name"]