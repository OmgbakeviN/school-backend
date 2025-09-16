from rest_framework import serializers
from .models import Subject, ClassSubject

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id","code","name","short_name"]

class ClassSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSubject
        fields = ["id","classroom","subject","coefficient","is_core"]

# Détail pour UI (avec infos matière)
class ClassSubjectDetailSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(source="subject.id", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    class Meta:
        model = ClassSubject
        fields = ["id","classroom","subject","coefficient","is_core","subject_id","subject_code","subject_name"]