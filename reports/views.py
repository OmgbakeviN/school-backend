import io, zipfile
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.template.loader import render_to_string

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import Term
from enrollments.models import Enrollment
from subjects.models import ClassSubject
from .models import ReportToken, AnnualReportToken
from .services import (
    compute_student_term, build_pdf_html, render_pdf_from_html, sha1_bytes, 
    compute_student_annual, build_standard_competition_ranks,
    build_pdf_html_annual
)
from grading.services import compute_student_term_preview, compute_class_term_preview

class StudentTermPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        enrollment_id = request.query_params.get("enrollment_id")
        term_id = request.query_params.get("term_id")
        if not enrollment_id or not term_id:
            return Response({"detail":"enrollment_id and term_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        data = compute_student_term_preview(int(enrollment_id), int(term_id))
        return Response(data)

class ClassTermPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        classroom_id = request.query_params.get("classroom_id")
        term_id = request.query_params.get("term_id")
        with_details = request.query_params.get("details","0") == "1"
        if not classroom_id or not term_id:
            return Response({"detail":"classroom_id and term_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        data = compute_class_term_preview(int(classroom_id), int(term_id), with_details)
        return Response(data)

class StudentPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollment_id = request.GET.get("enrollment")
        term_id = request.GET.get("term")
        if not enrollment_id or not term_id:
            return Response({"detail":"enrollment and term are required"}, status=400)

        payload = compute_student_term(int(enrollment_id), int(term_id))
        # token
        token = ReportToken.objects.create(
            enrollment_id=enrollment_id,
            term_id=term_id,
            payload=payload
        )
        verify_url = request.build_absolute_uri(reverse("report-verify", args=[str(token.uid)]))
        html = build_pdf_html(payload, verify_url)
        pdf = render_pdf_from_html(html)
        token.pdf_sha1 = sha1_bytes(pdf)
        token.save(update_fields=["pdf_sha1"])

        filename = f"{payload['student']['matricule']}_{payload['classroom']['name']}_T{payload['term']['index']}.pdf"
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{filename}"'
        return resp

class ClassPDFBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        classroom_id = request.GET.get("classroom")
        term_id = request.GET.get("term")
        if not classroom_id or not term_id:
            return Response({"detail":"classroom and term are required"}, status=400)

        enrollments = Enrollment.objects.filter(classroom_id=classroom_id, active=True).select_related("student","classroom__year")
        if not enrollments.exists():
            return Response({"detail":"No enrollments"}, status=404)

        memzip = io.BytesIO()
        with zipfile.ZipFile(memzip, "w", zipfile.ZIP_DEFLATED) as zf:
            for e in enrollments:
                payload = compute_student_term(e.id, int(term_id))
                token = ReportToken.objects.create(enrollment=e, term_id=term_id, payload=payload)
                verify_url = request.build_absolute_uri(reverse("report-verify", args=[str(token.uid)]))
                html = build_pdf_html(payload, verify_url)
                pdf = render_pdf_from_html(html)
                token.pdf_sha1 = sha1_bytes(pdf); token.save(update_fields=["pdf_sha1"])
                fname = f"{payload['student']['matricule']}_{payload['classroom']['name']}_T{payload['term']['index']}.pdf"
                zf.writestr(fname, pdf)

        memzip.seek(0)
        resp = HttpResponse(memzip.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="class_{classroom_id}_T{term_id}.zip"'
        return resp

class ReportVerifyPage(TemplateView):
    template_name = "reports/verify.html"
    permission_classes = [AllowAny]  # ignoré par CBV classique, mais page publique

    def get(self, request, uid):
        try:
            token = ReportToken.objects.select_related("enrollment__student","term","enrollment__classroom__year","enrollment__classroom__level").get(uid=uid)
        except ReportToken.DoesNotExist:
            raise Http404("Unknown report UID")
        ctx = {
            "valid": token.valid,
            "student": {
                "matricule": token.enrollment.student.matricule,
                "name": f"{token.enrollment.student.last_name} {token.enrollment.student.first_name}",
            },
            "classroom": token.enrollment.classroom.name,
            "year": token.enrollment.classroom.year.name,
            "term": token.term.index,
            "created_at": token.created_at,
            "pdf_sha1": token.pdf_sha1,
        }
        return self.render_to_response(ctx)

class StudentAnnualPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollment_id = request.GET.get("enrollment")
        if not enrollment_id:
            return Response({"detail":"enrollment is required"}, status=400)

        # 1) payload élève
        payload = compute_student_annual(int(enrollment_id))

        # 2) rangs (pas de récursion)
        classroom_id = payload["classroom"]["id"]
        enrollments = Enrollment.objects.filter(classroom_id=classroom_id, active=True)
        avg_map = {}
        cache = {}
        for e in enrollments:
            p = compute_student_annual(e.id) if e.id != int(enrollment_id) else payload
            cache[e.id] = p
            avg_map[e.id] = p["totals"]["average"]
        rank_map, class_avg = build_standard_competition_ranks(avg_map)
        payload["class_stats"] = {
            "rank": rank_map.get(int(enrollment_id)),
            "count": len(avg_map),
            "class_avg": class_avg
        }

        # 3) token + QR
        token = AnnualReportToken.objects.create(
            enrollment_id=enrollment_id,
            year_label=payload["classroom"]["year"],
            payload=payload
        )
        verify_url = request.build_absolute_uri(reverse("report-verify-annual", args=[str(token.uid)]))

        html = build_pdf_html_annual(payload, verify_url)
        pdf = render_pdf_from_html(html)
        token.pdf_sha1 = sha1_bytes(pdf)
        token.save(update_fields=["pdf_sha1"])

        filename = f"{payload['student']['matricule']}_{payload['classroom']['name']}_ANNUAL.pdf"
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{filename}"'
        return resp

class ClassAnnualPDFBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        classroom_id = request.GET.get("classroom")
        if not classroom_id:
            return Response({"detail":"classroom is required"}, status=400)

        enrollments = list(Enrollment.objects.filter(classroom_id=classroom_id, active=True).select_related("student","classroom__year"))
        if not enrollments:
            return Response({"detail":"No enrollments"}, status=404)

        # payloads + avg_map
        payloads, avg_map = {}, {}
        for e in enrollments:
            p = compute_student_annual(e.id)
            payloads[e.id] = p
            avg_map[e.id] = p["totals"]["average"]
        rank_map, class_avg = build_standard_competition_ranks(avg_map)

        memzip = io.BytesIO()
        with zipfile.ZipFile(memzip, "w", zipfile.ZIP_DEFLATED) as zf:
            for e in enrollments:
                p = payloads[e.id]
                p["class_stats"] = {
                    "rank": rank_map.get(e.id),
                    "count": len(avg_map),
                    "class_avg": class_avg
                }
                token = AnnualReportToken.objects.create(
                    enrollment=e,
                    year_label=p["classroom"]["year"],
                    payload=p
                )
                verify_url = request.build_absolute_uri(reverse("report-verify-annual", args=[str(token.uid)]))
                html = build_pdf_html_annual(p, verify_url)
                pdf = render_pdf_from_html(html)
                token.pdf_sha1 = sha1_bytes(pdf); token.save(update_fields=["pdf_sha1"])
                fname = f"{p['student']['matricule']}_{p['classroom']['name']}_ANNUAL.pdf"
                zf.writestr(fname, pdf)

        memzip.seek(0)
        resp = HttpResponse(memzip.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="class_{classroom_id}_ANNUAL.zip"'
        return resp

class AnnualReportVerifyPage(TemplateView):
    template_name = "reports/verify_annual.html"
    permission_classes = [AllowAny]  # page publique

    def get(self, request, uid):
        from .models import AnnualReportToken
        try:
            token = AnnualReportToken.objects.select_related(
                "enrollment__student", "enrollment__classroom__year", "enrollment__classroom__level"
            ).get(uid=uid)
        except AnnualReportToken.DoesNotExist:
            raise Http404("Unknown report UID")
        ctx = {
            "valid": token.valid,
            "student": {
                "matricule": token.enrollment.student.matricule,
                "name": f"{token.enrollment.student.last_name} {token.enrollment.student.first_name}",
            },
            "classroom": token.enrollment.classroom.name,
            "year": token.year_label,
            "created_at": token.created_at,
            "pdf_sha1": token.pdf_sha1,
        }
        return self.render_to_response(ctx)



