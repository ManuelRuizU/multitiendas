# plataforma_config/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlatformSettingViewSet

router = DefaultRouter()
router.register(r'configuracion', PlatformSettingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]