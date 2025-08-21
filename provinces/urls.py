from django.urls import path
from .views import check_province, province_suggestions

urlpatterns = [
    path('api/check/', check_province, name='province-check'),
    path('api/check/suggestions/', province_suggestions, name='province_suggestions-check'),
]