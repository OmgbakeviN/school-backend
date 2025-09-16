import io, base64, hashlib
from decimal import Decimal
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.db.models import Prefetch
from xhtml2pdf import pisa
import qrcode
from core.models import Classroom, Term
from subjects.models import ClassSubject
from enrollments.models import Enrollment, EnrollmentSubject
from assessments.models import Assessment, Score, AssessmentType
from grading.models import GradeBand, GradeScale
from reports.models import ReportToken

TIMES_STACK = '"Times New Roman", Times, serif'

def grade_for(score):
    # score peut arriver en float/Decimal → cast propre en Decimal
    try:
        score = Decimal(str(score))
    except Exception:
        return ""

    from grading.models import GradeBand  # import local pour éviter cycles
    band = (GradeBand.objects
            .select_related("scale")
            .filter(  
                min_mark__lte=score,
                max_mark__gte=score
            )
            .order_by("min_mark")
            .first())
    return band.letter if band else ""

def compute_student_term(enrollment_id: int, term_id: int):
    e = (Enrollment.objects
         .select_related("student","classroom__level","classroom__year")
         .get(id=enrollment_id))
    classroom = e.classroom
    level_code = (classroom.level.code or "").upper()
    term = Term.objects.get(id=term_id)

    # Matières de la classe (coef par défaut)
    cs_list = list(ClassSubject.objects.select_related("subject").filter(classroom=classroom))
    cs_by_id = {cs.id: cs for cs in cs_list}

    # Panier de l’élève (sélectionnées)
    es_list = list(EnrollmentSubject.objects
                   .filter(enrollment=e, selected=True, class_subject_id__in=cs_by_id.keys())
                   .select_related("class_subject__subject"))
    es_ids = [es.id for es in es_list]

    # Assessments (Term) + poids
    assessments = list(Assessment.objects.select_related("atype").filter(
        term_id=term_id, class_subject_id__in=cs_by_id.keys()))
    atype_by_aid = {a.id: a.atype for a in assessments}
    full_weight_by_cs = {}
    for a in assessments:
        full_weight_by_cs[a.class_subject_id] = full_weight_by_cs.get(a.class_subject_id, Decimal(0)) + Decimal(a.atype.weight)

    # Scores de l’élève ce term
    sc = list(Score.objects.filter(enrollment_subject_id__in=es_ids,
                                   assessment_id__in=[a.id for a in assessments])
              .values("assessment_id","enrollment_subject_id","value"))

    # Agrégat par ES
    num = {es.id: Decimal(0) for es in es_list}
    w_present = {es.id: Decimal(0) for es in es_list}
    for s in sc:
        w = Decimal(atype_by_aid[s["assessment_id"]].weight)
        num[s["enrollment_subject_id"]] += Decimal(s["value"]) * w
        w_present[s["enrollment_subject_id"]] += w

    # Lignes matières
    lines = []
    total_weighted = Decimal(0)
    total_coef = Decimal(0)

    for es in es_list:
        cs = es.class_subject
        coef = Decimal(es.coef_override or cs.coefficient)
        # Term mark (0..100) — F5/L6/U6: normaliser sur CA présentes; sinon sur poids total
        denom = w_present[es.id] if level_code in ("F5","L6","U6") else full_weight_by_cs.get(cs.id, Decimal(0))
        term_mark = (num[es.id] / denom) if denom > 0 else Decimal(0)
        weighted = term_mark * coef
        total_weighted += weighted
        total_coef += coef

        # Récup CA1/CA2 si existants (affichage)
        ca1 = ca2 = ""
        for a in assessments:
            if a.class_subject_id != cs.id: continue
            if a.atype.code == "CA1":
                val = next((Decimal(s["value"]) for s in sc if s["assessment_id"]==a.id and s["enrollment_subject_id"]==es.id), None)
                ca1 = float(val) if val is not None else ""
            if a.atype.code == "CA2":
                val = next((Decimal(s["value"]) for s in sc if s["assessment_id"]==a.id and s["enrollment_subject_id"]==es.id), None)
                ca2 = float(val) if val is not None else ""

        lines.append({
            "code": cs.subject.code,
            "name": cs.subject.name,
            "coef": float(coef),
            "ca1": ca1, "ca2": ca2,
            "mark": float(round(term_mark, 2)),
            "weighted": float(round(weighted, 2)),
            "grade": grade_for(term_mark),
        })

    avg = float(round((total_weighted / total_coef) if total_coef > 0 else 0, 2))

    payload = {
        "school": {
            "name": getattr(settings, "SCHOOL_NAME", "Your School"),
            "address": getattr(settings, "SCHOOL_ADDRESS", ""),
            "phone": getattr(settings, "SCHOOL_PHONE", ""),
        },
        "student": {
            "matricule": e.student.matricule,
            "name": f"{e.student.last_name} {e.student.first_name}",
            "sex": e.student.sex,
        },
        "classroom": {
            "name": classroom.name,
            "level": classroom.level.code,
            "year": classroom.year.name,
        },
        "term": {"id": term.id, "index": term.index},
        "lines": lines,
        "totals": {
            "coef_sum": float(total_coef),
            "weighted_sum": float(round(total_weighted, 2)),
            "average": avg,
        },
        # place-holders
        "attendance": {"absences": "", "lates": ""},
        "remarks": {"teacher": "", "principal": ""},
    }
    return payload

def make_qr_png_b64(text: str) -> str:
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")

def render_pdf_from_html(html: str) -> bytes:
    out = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=out)
    return out.getvalue()

def build_pdf_html(payload: dict, verify_url: str) -> str:
    # QR base64
    qr_b64 = make_qr_png_b64(verify_url)
    return render_to_string("reports/report_card.html", {
        "p": payload,
        "verify_url": verify_url,
        "qr_b64": qr_b64,
        "TIMES_STACK": TIMES_STACK,
    })

def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()
