from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from my_profile.views import ProfileViewSet, get_skills

router = DefaultRouter()
# in first have to get this url so according your selected_professional direct you to one of the below addresses
router.register('profile', ProfileViewSet, basename='profiles')

urlpatterns = [
    path('', include(router.urls)),
    path('skills/', get_skills, name='get-skills')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
