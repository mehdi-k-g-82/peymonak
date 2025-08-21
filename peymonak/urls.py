from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core.views import CustomTokenObtainPairView, VerifyCodeView
from rest_framework_simplejwt.views import TokenRefreshView
from register_ad.views import get_current_user
from core.views import request_verification_code  # Replace 'your_app' with your app name

urlpatterns = [
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('djoser.urls')),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('provinces/', include('provinces.urls')),
    path('my-profile/', include('my_profile.urls')),
    path('saved-ads/', include('saved_ads.urls')),
    path('support/', include('support.urls')),
    path('register-ad/', include('register_ad.urls')),
    path('api/user/', get_current_user, name='get_current_user'),
    path('api/verify/', VerifyCodeView.as_view(), name='verify_code'),  # Add this line
    path('api/request-verification/', request_verification_code, name='request_verification'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, show_indexes=True)
