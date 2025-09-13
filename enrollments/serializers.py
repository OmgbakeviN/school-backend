# enrollments/serializers.py
from rest_framework import serializers
from .models import Student, Enrollment, EnrollmentSubject

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id","matricule","last_name","first_name","sex","dob","house","photo_url"]

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id","student","classroom","active","date_enrolled"]
        read_only_fields = ["date_enrolled"]

class EnrollmentSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentSubject
        fields = ["id","enrollment","class_subject","coef_override","selected"]

# NOUVEAU : détaillé
class EnrollmentSubjectDetailSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(source="class_subject.subject.id", read_only=True)
    subject_code = serializers.CharField(source="class_subject.subject.code", read_only=True)
    subject_name = serializers.CharField(source="class_subject.subject.name", read_only=True)
    class_coefficient = serializers.DecimalField(source="class_subject.coefficient", max_digits=5, decimal_places=2, read_only=True)
    effective_coefficient = serializers.SerializerMethodField()

    class Meta:
        model = EnrollmentSubject
        fields = [
            "id","enrollment","selected","coef_override",
            "subject_id","subject_code","subject_name",
            "class_coefficient","effective_coefficient",
        ]

    def get_effective_coefficient(self, obj):
        return obj.coef_override if obj.coef_override is not None else obj.class_subject.coefficient
