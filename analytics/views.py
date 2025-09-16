from decimal import Decimal
from collections import defaultdict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch

from core.models import Term, Classroom
from subjects.models import ClassSubject
from enrollments.models import Enrollment, EnrollmentSubject
from assessments.models import Assessment, AssessmentType, Score

# Create your views here.

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def class_stats(request, classroom_id: int):
    term_id = request.GET.get("term")
    if not term_id:
        return Response({"detail": "term is required"}, status=400)
    pass_mark = Decimal(request.GET.get("pass_mark", "50"))

    # Contexte classe/term
    classroom = Classroom.objects.select_related("level", "year").get(id=classroom_id)
    term = Term.objects.get(id=term_id)
    level_code = (classroom.level.code or "").upper()

    # Matières de la classe
    cs_list = list(
        ClassSubject.objects.select_related("subject")
        .filter(classroom_id=classroom_id)
        .order_by("subject__name")
    )
    cs_by_id = {cs.id: cs for cs in cs_list}

    # Inscriptions actives
    enrollments = list(
        Enrollment.objects.select_related("student")
        .filter(classroom_id=classroom_id, active=True)
        .order_by("student__last_name", "student__first_name")
    )
    enroll_ids = [e.id for e in enrollments]

    # Panier par élève (only selected)
    es_rows = list(
        EnrollmentSubject.objects
        .filter(enrollment_id__in=enroll_ids, class_subject_id__in=cs_by_id.keys(), selected=True)
        .values("id", "enrollment_id", "class_subject_id", "coef_override")
    )
    es_by_id = {r["id"]: r for r in es_rows}
    es_ids_by_enroll = defaultdict(list)
    for r in es_rows:
        es_ids_by_enroll[r["enrollment_id"]].append(r["id"])

    # Épreuves du trimestre pour ces matières
    assessments = list(
        Assessment.objects.select_related("atype")
        .filter(term_id=term_id, class_subject_id__in=cs_by_id.keys())
    )
    assess_ids = [a.id for a in assessments]
    atype_by_assessment = {a.id: a.atype for a in assessments}

    # Poids cumulés (par matière) = dénominateur F1..F4
    cs_full_weight = defaultdict(Decimal)
    for a in assessments:
        cs_full_weight[a.class_subject_id] += Decimal(a.atype.weight)

    # Scores existants (pour le trimestre & ces paniers)
    scores = list(
        Score.objects.filter(assessment_id__in=assess_ids, enrollment_subject_id__in=es_by_id.keys())
        .values("assessment_id", "enrollment_subject_id", "value")
    )

    # Agrégat par ES (numerator/denominator)
    es_num = defaultdict(Decimal)
    es_w_present = defaultdict(Decimal)
    for s in scores:
        val = Decimal(s["value"])
        w = Decimal(atype_by_assessment[s["assessment_id"]].weight)
        es_num[s["enrollment_subject_id"]] += val * w
        es_w_present[s["enrollment_subject_id"]] += w

    # Note matière par ES (0..100)
    es_subject_mark = {}  # ES -> note matière normalisée
    for es_id, num in es_num.items():
        cs_id = es_by_id[es_id]["class_subject_id"]
        denom = es_w_present[es_id] if level_code in ("F5", "L6", "U6") else cs_full_weight[cs_id]
        if denom > 0:
            es_subject_mark[es_id] = (num / denom)

    # Moyennes élève (avec coefficients)
    per_student = []
    for e in enrollments:
        total = Decimal(0)
        coef_sum = Decimal(0)
        for es_id in es_ids_by_enroll.get(e.id, []):
            cs_id = es_by_id[es_id]["class_subject_id"]
            coef = Decimal(es_by_id[es_id]["coef_override"] or cs_by_id[cs_id].coefficient)
            if es_id in es_subject_mark:
                total += es_subject_mark[es_id] * coef
                coef_sum += coef
            else:
                if level_code not in ("F5", "L6", "U6"):  # F1..F4 → matière sans note = 0 mais comptée
                    coef_sum += coef
        avg = float((total / coef_sum) if coef_sum > 0 else 0)
        per_student.append({
            "enrollment_id": e.id,
            "student_id": e.student.id,
            "matricule": e.student.matricule,
            "student_name": f"{e.student.last_name} {e.student.first_name}",
            "avg": round(avg, 2),
        })

    # KPIs
    count_students = len(per_student)
    class_avg = round(sum(s["avg"] for s in per_student) / count_students, 2) if count_students else 0.0
    pass_count = sum(1 for s in per_student if s["avg"] >= float(pass_mark))
    pass_rate = round((pass_count / count_students) * 100, 2) if count_students else 0.0

    # Completion (remplissage des notes CA1/CA2 attendues)
    assessments_by_cs_count = defaultdict(int)
    for a in assessments:
        assessments_by_cs_count[a.class_subject_id] += 1
    expected_total = 0
    for es in es_rows:
        expected_total += assessments_by_cs_count[es["class_subject_id"]]
    completion_rate = round((len(scores) / expected_total) * 100, 2) if expected_total else 0.0

    # Top 3
    top3 = sorted(per_student, key=lambda x: x["avg"], reverse=True)[:3]

    # Perf par matière
    per_subject = []
    es_ids_by_cs = defaultdict(list)
    for es in es_rows:
        es_ids_by_cs[es["class_subject_id"]].append(es["id"])
    for cs_id, es_ids in es_ids_by_cs.items():
        if level_code in ("F5", "L6", "U6"):
            vals = [float(es_subject_mark[e]) for e in es_ids if e in es_subject_mark]
        else:
            vals = [float(es_subject_mark.get(e, Decimal(0))) for e in es_ids]
        avg = round(sum(vals) / len(vals), 2) if vals else 0.0
        per_subject.append({
            "class_subject_id": cs_id,
            "subject_code": cs_by_id[cs_id].subject.code,
            "subject_name": cs_by_id[cs_id].subject.name,
            "avg": avg
        })
    per_subject.sort(key=lambda x: x["subject_name"])

    # Distribution des moyennes (classes de 10)
    bins = [{"range": f"{i*10}-{(i+1)*10 - (0 if i<9 else 0)}", "count": 0} for i in range(10)]
    for s in per_student:
        idx = int(min(max(s["avg"], 0), 100)) // 10
        if idx == 10: idx = 9
        bins[idx]["count"] += 1

    return Response({
        "classroom": {"id": classroom.id, "name": classroom.name, "level": classroom.level.code, "year": classroom.year.name},
        "term": {"id": term.id, "index": term.index},
        "class_avg": class_avg,
        "pass_rate": pass_rate,
        "count_students": count_students,
        "completion_rate": completion_rate,
        "top_students": top3,
        "per_subject": per_subject,
        "distribution": bins,
        "students": per_student,  # utile si tu veux une table
    })