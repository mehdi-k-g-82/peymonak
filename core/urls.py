from django.urls import path
from .views import UserCreateView, VerifyCodeView, CustomTokenObtainPairView

urlpatterns = [
    path('auth/register/', UserCreateView.as_view(), name='register'),
    path('auth/verify/', VerifyCodeView.as_view(), name='verify'),
]