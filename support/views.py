from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SupportRequest
from .serializers import SupportRequestSerializer


class SupportRequestViewSet(viewsets.ModelViewSet):
    queryset = SupportRequest.objects.filter()
    serializer_class = SupportRequestSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access
    http_method_names = ['get']
