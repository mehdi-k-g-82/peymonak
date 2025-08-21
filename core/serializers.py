from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from utils.sms import send_verification_sms
import random
import re

User = get_user_model()

# Login serializer for JWT using phone number
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'] = serializers.CharField()
        # self.fields['password'] = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        # password = attrs.get('password')

        if not phone_number:
            raise serializers.ValidationError('شماره تلفن نمی‌تواند خالی باشد.')

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError('کاربری با این شماره تلفن یافت نشد.')

        # if not user.check_password(password):
        #     raise serializers.ValidationError('رمز عبور اشتباه است.')

        if not user.is_verified:
            raise serializers.ValidationError('حساب کاربری شما تأیید نشده است.')

        attrs['phone_number'] = user.phone_number
        return super().validate(attrs)

# Registration serializer
class CustomUserCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True, max_length=15)
    selected_professional = serializers.CharField(required=True)
    national_code = serializers.CharField(required=True, max_length=10)

    class Meta:
        model = User
        fields = ('selected_professional', 'phone_number', 'national_code')
        extra_kwargs = {
            'selected_professional': {'required': True},
            'phone_number': {'required': True},
            'national_code': {'required': True},
        }

    def validate_national_code(self, value):
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError('کدملی باید دقیقاً ۱۰ رقم باشد.')
        return value

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        national_code = attrs.get('national_code')

        if User.objects.filter(phone_number=phone_number).exists():
            # Allow updating existing user
            pass

        if User.objects.filter(national_code=national_code).exclude(phone_number=phone_number).exists():
            raise serializers.ValidationError('کدملی قبلاً ثبت شده است.')

        return attrs

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        try:
            user = User.objects.get(phone_number=phone_number)
            user.selected_professional = validated_data['selected_professional']
            user.national_code = validated_data['national_code']
            user.is_verified = True
            user.verification_code = None
            user.save()
            return user
        except User.DoesNotExist:
            user = User.objects.create(
                selected_professional=validated_data['selected_professional'],
                phone_number=phone_number,
                national_code=validated_data['national_code'],
                is_verified=True
            )
            user.verification_code = None
            user.save()
            return user

# Verification serializer
class VerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(phone_number=attrs['phone_number'])
        except User.DoesNotExist:
            raise serializers.ValidationError("کاربر یافت نشد.")
        if user.verification_code != attrs['code']:
            raise serializers.ValidationError("کد تأیید اشتباه است.")
        return attrs

    def save(self):
        user = User.objects.get(phone_number=self.validated_data['phone_number'])
        if user.verification_code == self.validated_data['code']:
            user.verification_code = None
            user.save()
        return user

# User details serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('selected_professional', 'phone_number', 'national_code')