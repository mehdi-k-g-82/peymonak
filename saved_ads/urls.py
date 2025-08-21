from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavedAdViewSet

router = DefaultRouter()
router.register(r'', SavedAdViewSet, basename='saved-ads')

urlpatterns = [
    path('', include(router.urls)),
]