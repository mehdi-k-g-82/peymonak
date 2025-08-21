from rest_framework import serializers
from .models import SavedAd, register_ad

class SavedAdSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    ad = serializers.PrimaryKeyRelatedField(queryset=register_ad.objects.all())
    # Add other fields like title, images if needed
    title = serializers.CharField(source='ad.title', read_only=True)
    images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SavedAd
        fields = ['id', 'ad', 'title', 'images']

    def get_images(self, obj):
        # Assuming RegisterAd has a related images field
        return [{'image': img.image.url} for img in obj.ad.images.all()]
