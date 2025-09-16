from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
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
