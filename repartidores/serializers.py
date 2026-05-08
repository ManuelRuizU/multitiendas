# repartidores/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
import logging

from usuarios.models import BuyerProfile, SellerProfile, Cliente, Direccion
from .models import Repartidor

logger = logging.getLogger(__name__)
User = get_user_model()


# ------------------------------------------------------------------
# 1. SERIALIZADOR DE USUARIO BÁSICO
# CORRECCIÓN: Renombrado de UserSerializer → RepartidorUserSerializer
# para evitar conflicto con usuarios.serializers.UserSerializer
# que tiene 9 campos (incluyendo is_cliente, is_vendedor, is_repartidor, roles)
# ------------------------------------------------------------------
class RepartidorUserSerializer(serializers.ModelSerializer):
    """
    Serializador básico de usuario para uso interno en la app repartidores.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


# ------------------------------------------------------------------
# 2. SERIALIZADOR DE REPARTIDOR
# ------------------------------------------------------------------
class RepartidorSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el modelo Repartidor.
    Incluye datos del usuario y tiendas asignadas.
    """
    user = RepartidorUserSerializer(read_only=True)
    tiendas_nombres = serializers.SerializerMethodField()
    esta_activo = serializers.ReadOnlyField()
    cantidad_pedidos_activos = serializers.ReadOnlyField()

    class Meta:
        model = Repartidor
        fields = [
            'id', 'user', 'telefono', 'vehiculo', 'foto',
            'estado', 'tiendas', 'tiendas_nombres',
            'esta_activo', 'cantidad_pedidos_activos',
            'notas', 'fecha_registro',
        ]
        read_only_fields = [
            'id', 'user', 'fecha_registro',
            'esta_activo', 'cantidad_pedidos_activos',
        ]

    def get_tiendas_nombres(self, obj):
        return [t.nombre for t in obj.tiendas.all()]


# ------------------------------------------------------------------
# 3. SERIALIZADOR DE PERFIL DE COMPRADOR
# ------------------------------------------------------------------
class BuyerProfileSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo BuyerProfile.
    """
    user = RepartidorUserSerializer(read_only=True)

    class Meta:
        model = BuyerProfile
        fields = '__all__'
        read_only_fields = ['user']


# ------------------------------------------------------------------
# 4. SERIALIZADOR DE PERFIL DE VENDEDOR
# ------------------------------------------------------------------
class SellerProfileSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo SellerProfile.
    """
    user = RepartidorUserSerializer(read_only=True)

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'telefono', 'rut',
            'razon_social', 'giro', 'direccion_fiscal', 'fecha_registro'
        ]
        read_only_fields = ['id', 'user', 'fecha_registro']


# ------------------------------------------------------------------
# 5. SERIALIZADOR DE CLIENTE
# ------------------------------------------------------------------
class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Cliente.
    """
    user_username = serializers.ReadOnlyField(source='user.username', allow_null=True)
    user_email = serializers.ReadOnlyField(source='user.email', allow_null=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'user_username', 'user_email',
            'first_name', 'last_name', 'email',
            'telefono', 'is_guest', 'guest_uuid'
        ]
        read_only_fields = ['id', 'is_guest', 'guest_uuid', 'user_username', 'user_email']


# ------------------------------------------------------------------
# 6. SERIALIZADOR DE DIRECCIÓN
# ------------------------------------------------------------------
class DireccionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Direccion con datos del cliente anidados.
    """
    cliente_info = ClienteSerializer(source='cliente', read_only=True)
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        write_only=True
    )
    etiqueta = serializers.CharField(required=False, allow_blank=True, max_length=150)
    principal = serializers.BooleanField(required=False)

    class Meta:
        model = Direccion
        fields = [
            'id', 'cliente', 'cliente_info', 'etiqueta',
            'calle', 'numero', 'tipo_propiedad',
            'departamento', 'block', 'nombre_condominio',
            'comuna', 'ciudad', 'region', 'codigo_postal',
            'latitud', 'longitud', 'validada', 'principal',
        ]
        read_only_fields = ['id', 'validada', 'cliente_info']

    def validate(self, attrs):
        principal = attrs.get('principal', False)
        cliente = attrs.get('cliente')
        if principal and cliente:
            existing = Direccion.objects.filter(cliente=cliente, principal=True)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({
                    "principal": "Ya existe una dirección principal para este cliente."
                })
        return attrs


# ------------------------------------------------------------------
# 7. SERIALIZADOR PARA CAMBIO DE CONTRASEÑA
# ------------------------------------------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializador para cambiar la contraseña de un usuario.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Las nuevas contraseñas no coinciden."}
            )
        return attrs