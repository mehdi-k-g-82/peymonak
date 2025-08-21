# my_profile/serializers.py
import jdatetime
from django.utils import timezone
from rest_framework import serializers
from .filters import COOPERATION_KIND
from .models import register_ad, RegisterAdImage, Register_Request
from my_profile.models import Profile
from django.conf import settings
from component.gender import GENDER_CHOICES
from component.provinces import PROVINCES
from component.skill import SKILL
import logging

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL

class RegisterAdImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterAdImage
        fields = ['image']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name', 'city', 'gender', 'skill', 'description', 'profile_picture']

class RegisterRequestSerializer(serializers.ModelSerializer):
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    sender_phone = serializers.CharField(read_only=True, allow_null=True)
    recipient_phone = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Register_Request
        fields = [
            'id', 'ad', 'ad_title', 'sender_user', 'recipient_user', 'message',
            'is_pending', 'acknowledged_at', 'is_accepted', 'sender_phone', 'recipient_phone'
        ]
        read_only_fields = ['sender_user', 'acknowledged_at', 'sender_phone', 'recipient_phone']

    def validate(self, data):
        if self.instance is not None:  # Update
            return data
        request = self.context['request']
        ad = data.get('ad')
        recipient_user = data.get('recipient_user')
        if not ad:
            raise serializers.ValidationError("Ad is required.")
        try:
            ad_instance = register_ad.objects.get(id=ad.id)
        except register_ad.DoesNotExist:
            raise serializers.ValidationError("Ad does not exist.")
        if ad_instance.user == request.user:
            raise serializers.ValidationError("You cannot send a request to your own ad.")
        if Register_Request.objects.filter(ad=ad, sender_user=request.user).exists():
            raise serializers.ValidationError("You have already requested this ad.")
        if recipient_user is None:
            raise serializers.ValidationError("Recipient user is required.")
        if recipient_user == request.user:
            raise serializers.ValidationError("Sender user cannot be the same as recipient user.")
        return data

    def create(self, validated_data):
        validated_data['sender_user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        is_accepted = validated_data.get('is_accepted', instance.is_accepted)
        instance.is_accepted = is_accepted
        instance.is_pending = False
        instance.waiting_for_status = False
        instance.acknowledged_at = timezone.now()
        if is_accepted:
            instance.sender_phone = instance.sender_user.phone_number
            instance.recipient_phone = instance.recipient_user.phone_number
        else:
            instance.sender_phone = None
            instance.recipient_phone = None
        instance.save()
        return instance

class RegisterAdListSerializer(serializers.ModelSerializer):
    images = RegisterAdImageSerializer(many=True, read_only=True)
    gender = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = register_ad
        fields = [
            'id', 'title', 'description', 'fee', 'province', 'city',
            'cooperation_kind', 'skill', 'images', 'gender', 'status',
            'name', 'phone_number', 'created_at', 'user_id'
        ]

    def get_gender(self, obj):
        try:
            profile = obj.user.worker_profile.get()
            return profile.gender
        except Profile.DoesNotExist:
            logger.warning(f"No profile found for user {obj.user.id}")
            return None

    def get_created_at(self, obj):
        jalali_date = jdatetime.date.fromgregorian(date=obj.created_at)
        return jalali_date.strftime('%Y/%m/%d')

    def to_representation(self, instance):
        logger.info(f"Serializing ad ID {instance.id}, user_id: {instance.user.id}")
        return super().to_representation(instance)

class AdDetailSerializer(serializers.ModelSerializer):
    images = RegisterAdImageSerializer(many=True, read_only=True)
    gender = serializers.SerializerMethodField()

    class Meta:
        model = register_ad
        fields = [
            'id', 'title', 'description', 'fee', 'province', 'city',
            'cooperation_kind', 'skill', 'images', 'gender', 'status',
            'name', 'phone_number', 'created_at'
        ]

    def get_gender(self, obj):
        try:
            profile = obj.user.worker_profile.get()
            return profile.gender
        except Profile.DoesNotExist:
            logger.warning(f"No profile found for user {obj.user.id}")
            return None

    def get_created_at(self, obj):
        jalali_date = jdatetime.date.fromgregorian(date=obj.created_at)
        return jalali_date.strftime('%Y/%m/%d')

class RegisterSerializer(serializers.ModelSerializer):
    images = RegisterAdImageSerializer(many=True, required=False, read_only=False)
    gender = serializers.CharField(read_only=True)

    class Meta:
        model = register_ad
        fields = ['title', 'description', 'fee', 'province', 'city', 'cooperation_kind', 'skill', 'images', 'gender']
        read_only_fields = ['phone_number', 'name', 'selected_professional', 'gender']

    def validate_province(self, value):
        valid_provinces = [p[0] for p in PROVINCES]
        if value not in valid_provinces:
            raise serializers.ValidationError(f"استان باید یکی از {valid_provinces} باشد.")
        return value

    def validate_cooperation_kind(self, value):
        valid_kinds = [k[0] for k in COOPERATION_KIND]
        if value not in valid_kinds:
            raise serializers.ValidationError(f"نوع همکاری باید یکی از {valid_kinds} باشد.")
        return value

    def validate_skill(self, value):
        valid_skills = [s[0] for s in SKILL]
        if value and value not in valid_skills:
            raise serializers.ValidationError(f"مهارت باید یکی از {valid_skills} باشد.")
        return value

    def validate_fee(self, value):
        if value != 'توافقی' and not value.isdigit():
            raise serializers.ValidationError("هزینه باید 'توافقی' یا یک مقدار عددی باشد.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user

        if not attrs.get('title'):
            raise serializers.ValidationError("عنوان آگهی الزامی است.")
        if not attrs.get('description'):
            raise serializers.ValidationError("توضیحات آگهی الزامی است.")
        if not attrs.get('province'):
            raise serializers.ValidationError("استان الزامی است.")
        if not attrs.get('fee'):
            raise serializers.ValidationError("هزینه الزامی است.")

        selected_professional = user.selected_professional
        cooperation_kind = attrs.get('cooperation_kind')
        if selected_professional == 'Worker':
            attrs['cooperation_kind'] = 'فرد'
        elif selected_professional in ['Constructor', 'Contractor']:
            if not cooperation_kind:
                raise serializers.ValidationError({"cooperation_kind": "نوع همکاری برای پیمانکار الزامی است."})
            if cooperation_kind not in ['فرد', 'شرکت']:
                raise serializers.ValidationError({"cooperation_kind": "نوع همکاری باید 'فرد' یا 'شرکت' باشد."})

        if selected_professional != 'Constructor' and not attrs.get('skill'):
            raise serializers.ValidationError("مهارت الزامی است.")

        try:
            profile = Profile.objects.get(user=user)
            attrs['gender'] = profile.gender
        except Profile.DoesNotExist:
            raise serializers.ValidationError("پروفایل کاربر یافت نشد. لطفاً ابتدا پروفایل خود را تکمیل کنید.")

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        if not user.is_authenticated:
            raise serializers.ValidationError("نیاز به احراز هویت. لطفا توکن معتبر ارائه دهید.")

        register_count = register_ad.objects.filter(user_id=user.id).count()
        if user.selected_professional == 'Constructor' and register_count >= 5:
            raise serializers.ValidationError("حداکثر ۵ آگهی برای پیمانکار مجاز است.")
        elif user.selected_professional in ['Contractor', 'Worker'] and register_count >= 1:
            raise serializers.ValidationError("فقط ۱ آگهی برای کارفرما یا کارگر مجاز است.")

        images_data = validated_data.pop('images', None)
        profile = Profile.objects.get(user=user)
        register_instance = register_ad.objects.create(
            user=user,
            name=profile.name,
            selected_professional=user.selected_professional,
            phone_number=user.phone_number,
            **validated_data
        )

        images = request.FILES.getlist('images') if request.FILES else []
        if len(images) > 5:
            raise serializers.ValidationError("حداکثر 5 تصویر مجاز است.")
        for image in images:
            RegisterAdImage.objects.create(register_ad=register_instance, image=image)

        logger.info(f"Ad created for user {user.id}, gender: {register_instance.gender}")
        return register_instance



class ActiveAdListSerializer(serializers.ModelSerializer):
    images = RegisterAdImageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = register_ad
        fields = [
            'id', 'title', 'description', 'phone_number', 'province', 'city',
            'cooperation_kind', 'skill', 'status', 'created_at', 'images',
            'user_name', 'user_id', 'gender'
        ]

    def get_created_at(self, obj):
        jalali_date = jdatetime.date.fromgregorian(date=obj.created_at)
        return jalali_date.strftime('%Y/%m/%d')
