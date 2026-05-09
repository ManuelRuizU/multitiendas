# plataforma_config/urls.py
from django.urls import path
from .views import PlatformSettingView, CategoriaTiendaListView

urlpatterns = [
    path('configuracion/',         PlatformSettingView.as_view(),      name='configuracion'),
    path('categorias-plataforma/', CategoriaTiendaListView.as_view(),  name='categorias-plataforma'),
]
