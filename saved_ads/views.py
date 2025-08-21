from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SavedAd
from .serializers import SavedAdSerializer
from django.db import IntegrityError
class SavedAdViewSet(viewsets.ModelViewSet):
    queryset = SavedAd.objects.all()
    serializer_class = SavedAdSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedAd.objects.filter(user=self.request.user).select_related('ad')

    def perform_create(self, serializer):
        # Save with the authenticated user
        serializer.save(user=self.request.user)
     