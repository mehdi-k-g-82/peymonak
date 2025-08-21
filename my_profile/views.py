from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .permission import DenyProfileDeletion
from .serializers import ProfileSerializer
from .models import Profile, Sample_image
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
import traceback
import uuid
import os
import io
from PIL import Image
from rest_framework.decorators import api_view

class ProfileViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, DenyProfileDeletion]

    def get_queryset(self):
        return Profile.objects.filter(user_id=self.request.user.id)

    def get_object(self):
        user_id = self.kwargs.get('pk')
        try:
            profile = Profile.objects.get(user_id=user_id)
            if profile.user_id != self.request.user.id:
                self.permission_denied(self.request, message="You can only access your own profile")
            return profile
        except Profile.DoesNotExist:
            return Response({"error": "پروفایل یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='public')
    def get_public_profile(self, request, pk=None):
        try:
            profile = Profile.objects.get(user_id=pk)
            public_data = {
                'user_id': profile.user_id,
                'full_name': f"{profile.name or 'ناشناس'}",
                'profile_picture': f"{settings.MEDIA_URL}{profile.profile_picture}" if profile.profile_picture else None,
            }
            return Response(public_data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"error": "پروفایل یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in get_public_profile: {e}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def list(self, request, *args, **kwargs):
    #     print(f"List request: {request.method} {request.get_full_path()}")
    #     try:
    #         profile = self.get_queryset().first()
    #         if not profile:
    #             return Response({"error": "پروفایل یافت نشد. لطفاً یک پروفایل ایجاد کنید."}, status=status.HTTP_404_NOT_FOUND)
    #         serializer = self.get_serializer(profile, context={'request': request})
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         print(f"Error in list: {e}")
    #         print(traceback.format_exc())
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        print(f"Create request data: {request.data}")
        print(f"Create request files: {request.FILES}")
        serializer = self.get_serializer(data=request.data, context={'request': request})
        try:
            if serializer.is_valid():
                profile_picture = request.FILES.get('profile_picture')
                sample_pictures = request.FILES.getlist('sample_pictures')

                print(f"Profile picture: {profile_picture}")
                print(f"Sample pictures: {[img.name for img in sample_pictures]}")

                if len(sample_pictures) > 5:
                    return Response(
                        {"error": "نمی‌توانید بیش از ۵ تصویر نمونه آپلود کنید."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if profile_picture:
                    img = Image.open(profile_picture)
                    if img.mode in ('RGBA', 'LA'):
                        img = img.convert('RGB')
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=75, optimize=True)
                    compressed_image = ContentFile(output.getvalue(), name=f"{uuid.uuid4()}_compressed.jpg")
                    serializer.validated_data['profile_picture'] = compressed_image

                with transaction.atomic():
                    profile = serializer.save()

                    if sample_pictures:
                        for image in sample_pictures:
                            img = Image.open(image)
                            if img.mode in ('RGBA', 'LA'):
                                img = img.convert('RGB')
                            output = io.BytesIO()
                            img.save(output, format='JPEG', quality=75, optimize=True)
                            compressed_image = ContentFile(output.getvalue(), name=f"{uuid.uuid4()}_compressed.jpg")
                            sample_path = os.path.join('profile/sample', compressed_image.name)
                            saved_path = default_storage.save(sample_path, compressed_image)
                            Sample_image.objects.create(profile=profile, image=saved_path)
                            print(f"Saved sample image: {saved_path}")

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Profile creation error: {e}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        print(f"Update request: {request.method} {request.get_full_path()}")
        profile = self.get_object()
        if profile.user_id != self.request.user.id:
            return Response({"error": "You can only update your own profile"}, status=status.HTTP_403_FORBIDDEN)

        print(f"Update request data: {request.data}")
        print(f"Update request files: {request.FILES}")
        serializer = self.get_serializer(profile, data=request.data, partial=True, context={'request': request})
        try:
            if serializer.is_valid():
                profile_picture = request.FILES.get('profile_picture')
                sample_pictures = request.FILES.getlist('sample_pictures')

                print(f"Profile picture: {profile_picture}")
                print(f"Sample pictures: {[img.name for img in sample_pictures]}")

                total_existing = profile.samples.count()
                total_new = len(sample_pictures)
                if total_existing + total_new > 5:
                    return Response(
                        {"error": "نمی‌توانید بیش از ۵ تصویر نمونه داشته باشید."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if profile_picture:
                    img = Image.open(profile_picture)
                    if img.mode in ('RGBA', 'LA'):
                        img = img.convert('RGB')
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=75, optimize=True)
                    compressed_image = ContentFile(output.getvalue(), name=f"{uuid.uuid4()}_compressed.jpg")
                    serializer.validated_data['profile_picture'] = compressed_image
                elif request.data.get('profile_picture') == '':
                    serializer.validated_data['profile_picture'] = None

                with transaction.atomic():
                    serializer.save()

                    if sample_pictures:
                        for image in sample_pictures:
                            img = Image.open(image)
                            if img.mode in ('RGBA', 'LA'):
                                img = img.convert('RGB')
                            output = io.BytesIO()
                            img.save(output, format='JPEG', quality=75, optimize=True)
                            compressed_image = ContentFile(output.getvalue(), name=f"{uuid.uuid4()}_compressed.jpg")
                            sample_path = os.path.join('profile/sample', compressed_image.name)
                            saved_path = default_storage.save(sample_path, compressed_image)
                            Sample_image.objects.create(profile=profile, image=saved_path)
                            print(f"Saved sample image: {saved_path}")

                updated_serializer = self.get_serializer(profile, context={'request': request})
                return Response(updated_serializer.data, status=status.HTTP_200_OK)
            else:
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Profile update error: {e}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        print(f"Profile deletion attempt: {request.method} {request.get_full_path()}")
        return Response(
            {"error": "حذف پروفایل مجاز نیست"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>\d+)')
    def destroy_image(self, request, pk=None, image_id=None):
        print(f"Destroy image request: {request.method} {request.get_full_path()}")
        try:
            profile = self.get_object()
            if profile.user_id != self.request.user.id:
                return Response({"error": "You can only delete your own images"}, status=status.HTTP_403_FORBIDDEN)

            try:
                sample_image = Sample_image.objects.get(id=image_id, profile=profile)
                image_path = os.path.join(settings.MEDIA_ROOT, str(sample_image.image))
                if os.path.exists(image_path):
                    os.remove(image_path)
                sample_image.delete()
                print(f"Deleted sample image: {image_path}")
                return Response({"status": "تصویر حذف شد"}, status=status.HTTP_200_OK)
            except Sample_image.DoesNotExist:
                return Response({"error": "تصویر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response({"error": "شناسه تصویر نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error in destroy_image: {e}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_skills(request):
    user = request.user
    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        skills = [{'value': value, 'label': label} for value, label in settings.SKILL]
        return Response({"skills": skills}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in get_skills: {e}")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)