# plataforma_config/urls.py
from django.urls import path
from .views import PlatformSettingView
 
urlpatterns = [
    path('configuracion/', PlatformSettingView.as_view(), name='configuracion'),
]
 