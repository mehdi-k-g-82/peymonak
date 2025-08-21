from rest_framework import serializers
from .models import SupportRequest


class SupportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportRequest
        fields = ['telegram_link', 'eitaa_link', 'email']
        read_only_fields = ['telegram_link', 'eitaa_link', 'email']


