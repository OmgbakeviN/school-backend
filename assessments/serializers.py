from rest_framework import serializers
from django.db import transaction
from decimal import Decimal, InvalidOperation

from .models import AssessmentType, Assessment, Score
from enrollments.models import EnrollmentSubject
from subjects.models import ClassSubject
from core.models import Term


# -------------------------
#  Model Serializers
# -------------------------

class AssessmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentType
        fields = ["id", "code", "name", "weight", "is_active"]


class AssessmentSerializer(serializers.ModelSerializer):
    # Expose à la fois l'ID du type et son code ("CA1"/"CA2") pour le front
    atype = serializers.CharField(source="atype.code", read_only=True)
    atype_id = serializers.IntegerField(source="atype.id", read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "term", "class_subject", "atype", "atype_id"]


class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = ["id", "enrollment_subject", "assessment", "value"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convertir Decimal -> float pour confort front (si COERCE_DECIMAL_TO_STRING n'est pas réglé)
        if data.get("value") is not None:
            try:
                data["value"] = float(data["value"])
            except Exception:
                pass
        return data

    def validate(self, data):
        es = data["enrollment_subject"]
        a = data["assessment"]
        # L'EnrollmentSubject doit appartenir à la même matière (ClassSubject) que l'Assessment
        if es.class_subject_id != a.class_subject_id:
            raise serializers.ValidationError(
                "EnrollmentSubject does not belong to the Assessment's ClassSubject."
            )
        # Valeur dans [0..100]
        v = data.get("value", None)
        if v is None:
            raise serializers.ValidationError("Score 'value' is required.")
        try:
            dv = Decimal(str(v))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Score 'value' must be a number.")
        if not (Decimal("0") <= dv <= Decimal("100")):
            raise serializers.ValidationError("Score 'value' must be between 0 and 100.")
        return data


# -------------------------
#  BULK SERIALIZERS
# -------------------------

class BulkAssessmentCreateSerializer(serializers.Serializer):
    """
    Création en lot d'Assessments pour un trimestre.
    - term: PK du Term
    - EITHER classroom: id  -> crée pour toutes les ClassSubject de cette classe
      OR     class_subjects: [ids]  -> crée uniquement pour ces ClassSubject
    - atypes: liste de codes (["CA1","CA2"]). Par défaut: CA1+CA2 actifs.
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

        # Types actifs uniquement
        atypes = list(AssessmentType.objects.filter(code__in=atype_codes, is_active=True))
        # Check robustesse: tous les codes demandés doivent exister/être actifs
        if {a.code for a in atypes} != set(atype_codes):
            raise serializers.ValidationError("Some assessment types not found or inactive.")

        # Récupération des ClassSubject
        if "classroom" in validated:
            cs_qs = ClassSubject.objects.filter(classroom_id=validated["classroom"])
        else:
            cs_qs = ClassSubject.objects.filter(id__in=validated["class_subjects"])

        created, existing = [], []
        for cs in cs_qs:
            for at in atypes:
                obj, was_created = Assessment.objects.get_or_create(
                    term=term, class_subject=cs, atype=at
                )
                (created if was_created else existing).append(obj.id)

        return {"created": created, "existing": existing}


class BulkScoresUpsertSerializer(serializers.Serializer):
    """
    Upsert des notes pour UNE épreuve.
    Deux façons de cibler l'épreuve :
      - assessment: <id>
      - term + class_subject + atype_code  (ex: term=1, class_subject=5, atype_code="CA1")

    Body:
    {
      "assessment": 10,                       // ou l'autre trio
      "entries": [
        { "enrollment_subject": 101, "value": 17.5 },
        { "enrollment_subject": 102, "value": 12 }
      ]
    }
    """
    assessment = serializers.IntegerField(required=False)
    term = serializers.IntegerField(required=False)
    class_subject = serializers.IntegerField(required=False)
    atype_code = serializers.CharField(required=False)
    entries = serializers.ListField(child=serializers.DictField(), allow_empty=True)

    def validate(self, attrs):
        a_id = attrs.get("assessment")
        term_id = attrs.get("term")
        cs_id = attrs.get("class_subject")
        at_code = attrs.get("atype_code")

        if not a_id and not (term_id and cs_id and at_code):
            raise serializers.ValidationError(
                "Provide 'assessment' or ('term','class_subject','atype_code')."
            )

        # Résoudre l'assessment cible
        if a_id:
            try:
                assessment = Assessment.objects.select_related("class_subject").get(id=a_id)
            except Assessment.DoesNotExist:
                raise serializers.ValidationError("Assessment not found.")
        else:
            try:
                assessment = Assessment.objects.select_related("class_subject", "atype").get(
                    term_id=term_id, class_subject_id=cs_id, atype__code__iexact=at_code
                )
            except Assessment.DoesNotExist:
                raise serializers.ValidationError(
                    "Assessment not found for given (term, class_subject, atype_code)."
                )

        attrs["assessment_obj"] = assessment

        # Validation basique des entrées
        for e in attrs.get("entries", []):
            if "enrollment_subject" not in e:
                raise serializers.ValidationError("Each entry must have 'enrollment_subject'.")
            if "value" not in e:
                raise serializers.ValidationError("Each entry must have 'value'.")
            # On laissera le cast Decimal/Range au moment du create() pour différencier les raisons de skip
        return attrs

    @transaction.atomic
    def create(self, validated):
        assessment = validated["assessment_obj"]
        cs_id = assessment.class_subject_id

        # Index des scores existants pour cette épreuve
        existing = {
            s.enrollment_subject_id: s for s in Score.objects.filter(assessment=assessment)
        }

        results = {"created": [], "updated": [], "skipped": []}

        for e in validated.get("entries", []):
            es_id = e.get("enrollment_subject")
            raw_val = e.get("value")

            # 1) Cast propre en Decimal
            try:
                val = Decimal(str(raw_val))
            except (InvalidOperation, TypeError):
                results["skipped"].append({"enrollment_subject": es_id, "reason": "Invalid value"})
                continue
            if not (Decimal("0") <= val <= Decimal("100")):
                results["skipped"].append({"enrollment_subject": es_id, "reason": "Out of range"})
                continue

            # 2) ES doit exister et correspondre au même ClassSubject que l'Assessment
            try:
                es = EnrollmentSubject.objects.select_related("class_subject").get(id=es_id)
            except EnrollmentSubject.DoesNotExist:
                results["skipped"].append({"enrollment_subject": es_id, "reason": "EnrollmentSubject not found"})
                continue
            if es.class_subject_id != cs_id:
                results["skipped"].append({"enrollment_subject": es_id, "reason": "Subject mismatch"})
                continue

            # 3) Upsert
            if es_id in existing:
                s = existing[es_id]
                if s.value != val:
                    s.value = val
                    s.save(update_fields=["value"])
                results["updated"].append(s.id)
            else:
                s = Score.objects.create(enrollment_subject=es, assessment=assessment, value=val)
                results["created"].append(s.id)

        return results
