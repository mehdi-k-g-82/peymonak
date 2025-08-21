from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from register_ad import views

router = DefaultRouter()
router.register(r'register', views.RegisterAdView, basename='register-ad')
router.register(r'register-request', views.RegisterRequestViewSet, basename='register-request')
router.register(r'report-request-corporate', views.ReportRegisterRequestViewSet, basename='report-request-corporate')

# For AdDetailView, since it's a detail view with a pk parameter, you might not need a separate router
# You can either use the router or a simple path(), but not both

urlpatterns = [
    path('', include(router.urls)),
    path('ad-details/<int:pk>/', views.AdDetailView.as_view(), name='ad-details'),
    path('provinces/', views.get_provinces, name='get_provinces'),
    path('skills/', views.get_skills, name='get_skills'),
    path('gender/', views.get_gender_choices, name='get_gender_choices'),
    path('active-ads/', views.ActiveAdListView.as_view(), name='active-ads'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, show_indexes=True)