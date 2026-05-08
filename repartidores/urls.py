# repartidores/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepartidorViewSet

router = DefaultRouter()
router.register(r'repartidores', RepartidorViewSet, basename='repartidor')

urlpatterns = [
    path('', include(router.urls)),
]






