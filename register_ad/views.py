# register_ad/views.py
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from core.models import CustomUser
from utils.sms import logger
from .permissions import IsOwner
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from core.serializers import UserSerializer
from .filters import RegisterAdFilter
from component.gender import GENDER_CHOICES
from component.provinces import PROVINCES
from component.skill import SKILL
from .models import register_ad, Register_Request
from rest_framework import viewsets, generics, status
from .serializers import RegisterSerializer, RegisterAdListSerializer, ActiveAdListSerializer, AdDetailSerializer, RegisterRequestSerializer
from rest_framework.parsers import MultiPartParser, FormParser

User = get_user_model()

@api_view(['GET'])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
def get_provinces(request):
    return Response(PROVINCES)

@api_view(['GET'])
def get_skills(request):
    return Response(SKILL)

@api_view(['GET'])
def get_gender_choices(request):
    return Response(GENDER_CHOICES)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 1000  # Default to 10
    page_size_query_param = 'page_size'


class RegisterRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ad']

    def get_queryset(self):
        queryset = Register_Request.objects.all()
        ad_id = self.request.query_params.get('ad')
        sender_user = self.request.query_params.get('sender_user')
        recipient_user = self.request.query_params.get('recipient_user')

        if ad_id:
            queryset = queryset.filter(ad_id=ad_id)

        if sender_user:
            try:
                sender_user_id = int(sender_user)
                queryset = queryset.filter(sender_user_id=sender_user_id)
            except ValueError:
                raise ValidationError("Invalid sender_user ID")
        elif recipient_user:
            try:
                recipient_user_id = int(recipient_user)
                queryset = queryset.filter(recipient_user_id=recipient_user_id)
            except ValueError:
                raise ValidationError("Invalid recipient_user ID")
        else:
            queryset = queryset.filter(sender_user=self.request.user) | queryset.filter(recipient_user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        recipient_user_id = self.request.data.get('recipient_user')
        if not recipient_user_id:
            raise ValidationError("Recipient user ID is required.")
        try:
            recipient_user = CustomUser.objects.get(id=recipient_user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError(f"User with ID {recipient_user_id} does not exist.")
        serializer.save(sender_user=self.request.user, recipient_user=recipient_user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.recipient_user_id != request.user.id:
            return Response({"error": "Only the recipient can modify this request"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReportRegisterRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterRequestSerializer
    permission_classes = [IsAuthenticated]


class RegisterAdView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RegisterAdFilter
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.action == 'retrieve':
            logger.info(f"Retrieve ad ID {self.kwargs.get('pk')} for user {self.request.user.id}")
            queryset = register_ad.objects.prefetch_related('images').all()
            logger.info(f"Retrieve queryset: {queryset.count()} ads, IDs: {[ad.id for ad in queryset]}")
            return queryset
        elif self.action == 'list':
            logger.info(f"List ads for user {self.request.user.id}")
            return register_ad.objects.prefetch_related('images').all()
        logger.info(f"Restricted action {self.action} for user {self.request.user.id}")
        return register_ad.objects.prefetch_related('images').filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            logger.info(f"Applying IsOwner for action {self.action}")
            return [IsAuthenticated(), IsOwner()]
        logger.info(f"Applying IsAuthenticated for action {self.action}")
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RegisterAdListSerializer
        return RegisterSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        user = self.request.user
        logger.info(f"Creating ad for user {user.id}, data: {self.request.data}")
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"Ad created successfully for user {user.id}, gender: {serializer.instance.gender}")
        except ValidationError as e:
            logger.error(f"Ad creation failed for user {user.id}, errors: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ad creation for user {user.id}: {e}")
            raise ValidationError(str(e))

    def destroy(self, request, *args, **kwargs):
        logger.info(f"Attempting to delete ad ID {self.kwargs.get('pk')} for user {request.user.id}")
        try:
            instance = self.get_object()
            # Log ad details before deletion
            logger.info(
                f"Deleting ad ID {instance.id}: title={instance.title}, user_id={instance.user_id}, images_count={instance.images.count()}")

            # Explicitly delete image files from storage
            for image in instance.images.all():
                if image.image:
                    logger.info(f"Deleting image file: {image.image.name}")
                    image.image.delete(save=False)  # Delete file from storage
                image.delete()  # Delete image record from database

            # Delete the ad (database CASCADE should handle related records, but images are already deleted above)
            self.perform_destroy(instance)
            logger.info(f"Ad ID {instance.id} and associated images deleted successfully")
            return Response(status=204)
        except register_ad.DoesNotExist:
            logger.error(f"Ad ID {self.kwargs.get('pk')} not found")
            return Response({"detail": "آگهی یافت نشد"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting ad ID {self.kwargs.get('pk')}: {str(e)}")
            return Response({"detail": f"خطای سرور: {str(e)}"}, status=500)

    def retrieve(self, request, *args, **kwargs):
        logger.info(f"Attempting to retrieve ad ID {kwargs.get('pk')}")
        try:
            instance = self.get_object()
            logger.info(
                f"Found ad ID {kwargs.get('pk')}: title={instance.title}, user_id={instance.user_id}, status={instance.status}")
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except register_ad.DoesNotExist:
            logger.error(f"Ad ID {kwargs.get('pk')} not found in queryset")
            return Response({"detail": "آگهی یافت نشد"}, status=404)
        except Exception as e:
            logger.error(f"Retrieve error for ad ID {kwargs.get('pk')}: {str(e)}")
            return Response({"detail": "خطای سرور"}, status=500)


class ActiveAdListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = ActiveAdListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RegisterAdFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = register_ad.objects.prefetch_related('images').filter(status='active')
        logger.info(f"Active ads queryset: {queryset.count()} ads, IDs: {[ad.id for ad in queryset]}")
        return queryset

class AdDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = AdDetailSerializer
    queryset = register_ad.objects.prefetch_related('images').all()
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.info(f"AdDetailView: Found ad ID {kwargs.get('pk')}: title={instance.title}, user_id={instance.user_id}, status={instance.status}")
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except register_ad.DoesNotExist:
            logger.error(f"AdDetailView: Ad ID {kwargs.get('pk')} not found")
            return Response({"detail": "آگهی یافت نشد"}, status=404)
        except Exception as e:
            logger.error(f"AdDetailView: Error for ad ID {kwargs.get('pk')}: {str(e)}")
            return Response({"detail": "خطای سرور"}, status=500)