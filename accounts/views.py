from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from .serializers import MeSerializer

# Create your views here.
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(MeSerializer(request.user).data)

class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status":"ok"})