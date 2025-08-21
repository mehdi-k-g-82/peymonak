from rest_framework import serializers
from .models import Profile, Sample_image
from component.gender import GENDER_CHOICES
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SkillSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()

class SampleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample_image
        fields = ['id', 'image']

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     if instance.image:
    #         image_url = f"{settings.MEDIA_URL}{instance.image}"
    #         if not image_url.startswith('http'):
    #             image_url = f"{self.context['request'].scheme}://{self.context['request'].get_host()}{image_url}"
    #         representation['image'] = image_url
    #     else:
    #         representation['image'] = ''
    #     return representation

class ProfileSerializer(serializers.ModelSerializer):
    sample_images = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user', 'name', 'gender', 'city',
            'description', 'skill', 'profile_picture', 'sample_images'
        ]
        read_only_fields = ['user']

    def get_sample_images(self, obj):
        sample_images = obj.samples.all()
        return SampleImageSerializer(sample_images, many=True, context=self.context).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.profile_picture:
            profile_picture_url = f"{settings.MEDIA_URL}{instance.profile_picture}"
            if not profile_picture_url.startswith('http'):
                profile_picture_url = f"{self.context['request'].scheme}://{self.context['request'].get_host()}{profile_picture_url}"
            representation['profile_picture'] = profile_picture_url
        else:
            representation['profile_picture'] = ''
        logger.info(f"Serialized profile for user {instance.user_id}, gender: {representation['gender']}")
        return representation

    def validate_gender(self, value):
        valid_genders = [g[0] for g in GENDER_CHOICES]
        if value and value not in valid_genders:
            logger.error(f"Invalid gender value: {value}, expected one of {valid_genders}")
            raise serializers.ValidationError(f"جنسیت باید یکی از {valid_genders} باشد.")
        return value

    def validate(self, data):
        data['gender'] = self.validate_gender(data.get('gender'))
        logger.info(f"Validated profile data for user {self.context['request'].user.id}: {data}")
        return data

    def create(self, validated_data):
        validated_data.pop('sample_images', None)
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError("Authenticated user is required to create a profile.")
        profile = Profile.objects.create(user=user, **validated_data)
        logger.info(f"Created profile for user {user.id}, gender: {profile.gender}")
        return profile