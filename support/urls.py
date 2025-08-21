from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportRequestViewSet

router = DefaultRouter()
router.register('', SupportRequestViewSet, basename='support')

urlpatterns = [
    path('', include(router.urls)),
]