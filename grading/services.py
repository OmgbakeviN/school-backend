from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

from core.models import Term, Level
from subjects.models import ClassSubject
from enrollments.models import Enrollment, EnrollmentSubject
from assessments.models import Assessment, AssessmentType, Score
from grading.models import GradeScale, GradeBand

D0 = Decimal("0")
D100 = Decimal("100")

def _q(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def grade_letter(year, mark):
    """Retourne lettre à partir de la première GradeScale de l'année (ou None)."""
    mark_int = int(Decimal(mark).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    scale = GradeScale.objects.filter(year=year).first()
    if not scale:
        return None
    band = GradeBand.objects.filter(scale=scale, min_mark__lte=mark_int, max_mark__gte=mark_int).first()
    return band.letter if band else None

def is_level_F5_plus(level_code: str) -> bool:
    return level_code in ("F5","L6","U6")

def compute_student_term_preview(enrollment_id: int, term_id: int):
    """
    Calcule le récapitulatif trimestriel d'un élève.
    Règles:
      - Note matière (term) = moyenne pondérée des CA (weights = AssessmentType.weight)
      - F1–F4: CA manquant = 0; toutes les matières de la classe sont comptées
      - F5/L6/U6: on compte seulement les matières avec au moins une note;
                  pondération renormalisée sur les CA présents
    Retourne un dict structuré pour le JSON de preview.
    """
    enrollment: Enrollment = Enrollment.objects.select_related(
        "classroom__year", "classroom__level"
    ).get(id=enrollment_id)
    term: Term = Term.objects.select_related("year").get(id=term_id)
    classroom = enrollment.classroom
    level_code = classroom.level.code
    year = classroom.year

    # Tous les atypes actifs (ex CA1, CA2) et leurs poids
    atypes = list(AssessmentType.objects.filter(is_active=True).order_by("code"))
    weight_map = {a.id: _q(a.weight) for a in atypes}  # ex {id_CA1: 50, id_CA2: 50}

    # Matières suivies par l'élève (Option A = EnrollmentSubject sélectionnés)
    es_qs = (EnrollmentSubject.objects
             .filter(enrollment=enrollment, selected=True)
             .select_related("class_subject__subject"))
    es_by_cs = {es.class_subject_id: es for es in es_qs}

    # Toutes les class_subject de la classe (utile pour F1–F4)
    cs_qs = (ClassSubject.objects
             .filter(classroom=classroom)
             .select_related("subject"))

    # Assessments de ce term pour la classe
    ass_qs = (Assessment.objects
              .filter(term=term, class_subject__classroom=classroom)
              .select_related("class_subject__subject","atype"))

    # Scores de l'élève pour ces assessments
    scores = (Score.objects
              .filter(enrollment_subject__enrollment=enrollment, assessment__in=ass_qs)
              .select_related("assessment__atype","enrollment_subject","assessment"))

    # Indexation
    assessments_by_cs = defaultdict(list)
    for a in ass_qs:
        assessments_by_cs[a.class_subject_id].append(a)

    score_map = {}  # (assessment_id) -> value
    for s in scores:
        score_map[s.assessment_id] = _q(s.value)

    details = []
    sum_weighted = D0
    sum_coefs = D0

    for cs in cs_qs:
        subject = cs.subject
        es = es_by_cs.get(cs.id)  # None si élève n'a pas pris cette matière (F5+)
        coef_effective = _q(es.coef_override) if (es and es.coef_override is not None) else _q(cs.coefficient)

        a_list = assessments_by_cs.get(cs.id, [])
        if not a_list:
            # pas d'assessment configuré pour cette matière et term -> ignorer
            continue

        # Récupérer les notes
        present_weights = D0
        acc = D0
        for a in a_list:
            w = weight_map.get(a.atype_id, D0)
            v = score_map.get(a.id, None)
            if v is None:
                continue
            present_weights += w
            acc += (v * w)

        if is_level_F5_plus(level_code):
            # on compte la matière seulement si au moins une note est présente
            if present_weights == D0:
                # aucune note -> ignorer du calcul global
                continue
            term_mark = (acc / present_weights)  # renormalisation
        else:
            # F1–F4: manquants = 0, dénominateur = somme des poids définis
            total_w = sum(weight_map.values()) or Decimal("100")
            term_mark = (acc / (present_weights if present_weights > D0 else D0)) if present_weights > D0 else D0
            # si des CA manquent, ils apportent 0: rien à ajouter, mais denominator doit être total_w
            term_mark = (acc / (present_weights if present_weights > D0 else D0)).quantize(Decimal("0.01")) if present_weights > D0 else D0
            # puis on remet à l'échelle par total_w/present_weights si nécessaire
            if present_weights and present_weights != total_w:
                term_mark = (term_mark * (present_weights / total_w)).quantize(Decimal("0.01"))
            # si aucun CA présent, term_mark reste 0

        term_mark = _q(term_mark)
        letter = grade_letter(year, term_mark) or ""

        details.append({
            "subject_id": subject.id,
            "subject_code": subject.code,
            "subject_name": subject.name,
            "coefficient": float(coef_effective),
            "ca": [
                {"code": a.atype.code, "weight": float(weight_map.get(a.atype_id, D0)), "value": float(score_map.get(a.id)) if score_map.get(a.id) is not None else None}
                for a in sorted(a_list, key=lambda x: x.atype.code)
            ],
            "term_mark": float(term_mark),
            "grade": letter,
            "included_in_average": True if (not is_level_F5_plus(level_code) or (is_level_F5_plus(level_code) and present_weights > D0)) else False,
        })

        # Agrégats
        if (not is_level_F5_plus(level_code)) or (is_level_F5_plus(level_code) and present_weights > D0):
            sum_weighted += (coef_effective * term_mark)
            sum_coefs += coef_effective

    general_average = float(_q(sum_weighted / sum_coefs)) if sum_coefs > D0 else 0.0
    general_grade = grade_letter(year, general_average) or ""

    return {
        "enrollment_id": enrollment.id,
        "student": {
            "id": enrollment.student.id,
            "matricule": enrollment.student.matricule,
            "name": f"{enrollment.student.last_name} {enrollment.student.first_name}",
        },
        "classroom": {
            "id": classroom.id,
            "name": classroom.name,
            "level": classroom.level.code,
            "year": classroom.year.name,
        },
        "term": {"id": term.id, "index": term.index, "year": term.year.name},
        "subjects": details,   # pour le tableau PDF
        "sum_coefficients": float(_q(sum_coefs)),
        "weighted_total": float(_q(sum_weighted)),
        "general_average": general_average,
        "general_grade": general_grade,
    }

def compute_class_term_preview(classroom_id: int, term_id: int, with_details=False):
    """
    Calcule la moyenne de chaque élève de la classe pour un term.
    with_details=False -> renvoie lignes compactes (plus rapide pour tableau).
    """
    term = Term.objects.select_related("year").get(id=term_id)
    enrollments = (Enrollment.objects
                   .select_related("student","classroom__level","classroom__year")
                   .filter(classroom_id=classroom_id, active=True)
                   .order_by("student__last_name","student__first_name"))

    rows = []
    for e in enrollments:
        data = compute_student_term_preview(e.id, term.id)
        if with_details:
            rows.append(data)
        else:
            rows.append({
                "enrollment_id": data["enrollment_id"],
                "student": data["student"],
                "general_average": data["general_average"],
                "general_grade": data["general_grade"],
            })

    # Classement simple par moyenne (desc)
    rows_sorted = sorted(rows, key=lambda x: x["general_average"], reverse=True)
    # injecter rank
    for i, r in enumerate(rows_sorted, start=1):
        r["rank"] = i

    return {
        "classroom_id": classroom_id,
        "term": {"id": term.id, "index": term.index, "year": term.year.name},
        "count": len(rows_sorted),
        "results": rows_sorted,
    }
