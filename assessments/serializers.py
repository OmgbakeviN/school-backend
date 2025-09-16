from rest_framework import serializers
from django.db import transaction
from .models import AssessmentType, Assessment, Score
from enrollments.models import EnrollmentSubject
from subjects.models import ClassSubject
from core.models import Term

class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = ["id", "code", "name", "weight", "is_active"]

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ["id", "term", "class_subject", "atype"]

    def validate(self, data):
        # Rien de spécial ici; l'unicité est gérée par unique_together
        return data

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = ["id", "enrollment_subject", "assessment", "value"]

    def validate(self, data):
        es = data["enrollment_subject"]
        a = data["assessment"]
        # Sécurité: l'enrollment_subject doit correspondre au même class_subject
        if es.class_subject_id != a.class_subject_id:
            raise serializers.ValidationError("EnrollmentSubject does not belong to the Assessment's ClassSubject.")
        return data

# -------- BULK SERIALIZERS --------

class BulkAssessmentCreateSerializer(serializers.Serializer):
    """
    Crée en lot des Assessments pour un term donné.
    - Soit on passe classroom (id) pour TOUTES les ClassSubject de la classe
    - Soit on passe class_subjects: [ids]
    - atypes: liste de codes (ex: ["CA1","CA2"]) — par défaut CA1+CA2
    """
    term = serializers.PrimaryKeyRelatedField(queryset=Term.objects.all())
    classroom = serializers.IntegerField(required=False)
    class_subjects = serializers.ListField(child=serializers.IntegerField(), required=False)
    atypes = serializers.ListField(child=serializers.CharField(), required=False)

    def validate(self, attrs):
        if not attrs.get("classroom") and not attrs.get("class_subjects"):
            raise serializers.ValidationError("Provide either 'classroom' or 'class_subjects'.")
        return attrs

    @transaction.atomic
    def create(self, validated):
        term = validated["term"]
        atype_codes = validated.get("atypes") or ["CA1", "CA2"]
        atypes = list(AssessmentType.objects.filter(code__in=atype_codes, is_active=True))
        if len(atypes) != len(set(atype_codes)):
            raise serializers.ValidationError("Some assessment types not found or inactive.")

        # Récupère les class_subjects (par classe ou par liste)
        cs_qs = ClassSubject.objects.none()
        if "classroom" in validated:
            cs_qs = ClassSubject.objects.filter(classroom_id=validated["classroom"])
        else:
            cs_qs = ClassSubject.objects.filter(id__in=validated["class_subjects"])

        created, existing = [], []
        for cs in cs_qs:
            for at in atypes:
                obj, was_created = Assessment.objects.get_or_create(term=term, class_subject=cs, atype=at)
                (created if was_created else existing).append(obj.id)
        return {"created": created, "existing": existing}

class BulkScoresUpsertSerializer(serializers.Serializer):
    """
    Upsert de notes pour UN assessment (ou spécification term+class_subject+atype_code).
    entries: [{ enrollment_subject: id, value: 0..100 }, ...]
    """
    assessment = serializers.IntegerField(required=False)
    term = serializers.IntegerField(required=False)
    class_subject = serializers.IntegerField(required=False)
    atype_code = serializers.CharField(required=False)
    entries = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate(self, attrs):
        a_id = attrs.get("assessment")
        term_id = attrs.get("term")
        cs_id = attrs.get("class_subject")
        at_code = attrs.get("atype_code")

        if not a_id and not (term_id and cs_id and at_code):
            raise serializers.ValidationError("Provide 'assessment' or ('term','class_subject','atype_code').")

        # Résoudre l'assessment cible
        if a_id:
            try:
                assessment = Assessment.objects.select_related("class_subject").get(id=a_id)
            except Assessment.DoesNotExist:
                raise serializers.ValidationError("Assessment not found.")
        else:
            try:
                assessment = Assessment.objects.select_related("class_subject").get(
                    term_id=term_id, class_subject_id=cs_id, atype__code=at_code
                )
            except Assessment.DoesNotExist:
                raise serializers.ValidationError("Assessment not found for given (term, class_subject, atype_code).")

        attrs["assessment_obj"] = assessment

        # Vérifier les entries
        for e in attrs["entries"]:
            if "enrollment_subject" not in e or "value" not in e:
                raise serializers.ValidationError("Each entry must have 'enrollment_subject' and 'value'.")
            if not (0 <= float(e["value"]) <= 100):
                raise serializers.ValidationError("Score 'value' must be between 0 and 100.")

        return attrs

    @transaction.atomic
    def create(self, validated):
        assessment = validated["assessment_obj"]
        cs_id = assessment.class_subject_id

        # Map existing scores for upsert
        existing = { (s.enrollment_subject_id): s for s in Score.objects.filter(assessment=assessment) }

        results = {"created": [], "updated": [], "skipped": []}
        for e in validated["entries"]:
            es_id = e["enrollment_subject"]
            val = e["value"]

            # sécurité: ES doit appartenir au même class_subject
            try:
                es = EnrollmentSubject.objects.select_related("class_subject").get(id=es_id)
            except EnrollmentSubject.DoesNotExist:
                results["skipped"].append({"enrollment_subject": es_id, "reason": "EnrollmentSubject not found"})
                continue
            if es.class_subject_id != cs_id:
                results["skipped"].append({"enrollment_subject": es_id, "reason": "Subject mismatch"})
                continue

            if es_id in existing:
                s = existing[es_id]
                s.value = val
                s.save(update_fields=["value"])
                results["updated"].append(s.id)
            else:
                s = Score.objects.create(enrollment_subject=es, assessment=assessment, value=val)
                results["created"].append(s.id)

        return results
