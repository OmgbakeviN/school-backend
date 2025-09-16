from rest_framework import serializers
from .models import AcademicYear, Term, Level, Stream, Classroom

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ["id","name","start_date","end_date"]

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ["id","year","index"]

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id","code","name"]

class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ["id","name","is_active"]

class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ["id","year","level","stream","name"]
