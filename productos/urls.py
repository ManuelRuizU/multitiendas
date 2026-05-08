# productos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, SubCategoriaViewSet, ProductoViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'subcategorias', SubCategoriaViewSet, basename='subcategoria')
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    path('', include(router.urls)),
]




