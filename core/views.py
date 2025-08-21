import json
import random
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from melipayamak import Api
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import CustomUser
from .serializers import CustomUserCreateSerializer, VerificationSerializer, CustomTokenObtainPairSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)


# Login view for JWT using phone number
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Registration view
class UserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "لطفاً کد تأیید ارسال‌شده به شماره تلفن خود را وارد کنید.",
            "phone_number": user.phone_number,
            "national_code": user.national_code
        }, status=status.HTTP_201_CREATED)



@csrf_exempt
def request_verification_code(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            logger.info(f"Received request body: {body}")
            phone_number = body.get('phone_number')
            logger.info(f"Extracted phone_number: {phone_number}")

            if not phone_number:
                logger.error("No phone_number provided in request")
                return JsonResponse({'error': 'شماره تلفن اجباری است.'}, status=400)

            # Validate number: 09xxxxxxxxx or 989xxxxxxxxx
            if not re.match(r'^(09\d{9}|989\d{9})$', phone_number):
                logger.error(f"Invalid phone number format: {phone_number}")
                return JsonResponse({'error': 'فرمت شماره تلفن معتبر نیست.'}, status=400)

            # Use phone_number as-is for SMS recipient
            recipient = phone_number

            # Create or get user (store raw user input)
            user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
            verification_code = str(random.randint(100000, 999999))
            user.verification_code = verification_code
            user.save()

            # If already verified
            if not created and user.is_verified:
                logger.info(f"User {phone_number} is already verified")
                return JsonResponse({
                    'message': 'کاربر قبلاً تأیید شده است. لطفاً کد تأیید را وارد کنید.',
                    'is_verified': True,
                    'phone_number': phone_number
                })

            # Send verification code via Meli Payamak
            try:
                api = Api(username, password)
                sms = api.sms()
                text = f'کد تأیید شما: {verification_code}'
                response = sms.send(recipient, _from, text)
                logger.info(f"Meli Payamak response for {recipient}: {response}")

                if isinstance(response, dict) and response.get('RetStatus') != 1:
                    logger.error(f"Meli Payamak failed to send SMS: {response}")
                    return JsonResponse({
                        'error': f'خطا در ارسال پیامک: {response.get("StrRetStatus", "Unknown error")}'
                    }, status=500)
            except Exception as e:
                logger.error(f"Meli Payamak error: {str(e)}")
                return JsonResponse({'error': f'خطا در ارسال پیامک: {str(e)}'}, status=500)

            logger.info(f"Verification code {verification_code} sent to {recipient}.")
            return JsonResponse({
                'message': 'کد تأیید با موفقیت ارسال شد.',
                'is_verified': False,
                'phone_number': phone_number
            })

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'داده‌های ارسالی نامعتبر است.'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    logger.warning("Method not allowed")
    return JsonResponse({'error': 'فقط روش POST مجاز است.'}, status=405)

# Verification view
class VerifyCodeView(generics.GenericAPIView):
    serializer_class = VerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        logger.info(f"Received data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Check if the code is valid
        if user.verification_code is None:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            response_data = {
                "message": "کد تأیید با موفقیت تأیید شد.",
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
            # Redirect based on is_verified status
            if user.is_verified:
                response_data["redirect_to"] = "login"
            else:
                response_data["redirect_to"] = "register"
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "حساب کاربری شما تأیید نشده است.",
            }, status=status.HTTP_400_BAD_REQUEST)

# User detail view for /auth/users/<pk>/
class UserDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'