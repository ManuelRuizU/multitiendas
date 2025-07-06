# usuarios/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion

# Serializador para el modelo User (solo campos básicos)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['username'] # Generalmente no permites cambiar el username por API una vez creado

# Serializador para PerfilVendedor
class PerfilVendedorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Incluye los datos del usuario relacionado, solo para lectura
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True) # Para crear/actualizar vinculando un User existente

    class Meta:
        model = PerfilVendedor
        fields = [
            'id', 'user', 'user_id', 'telefono', 'rut', 'razon_social',
            'giro', 'direccion_fiscal', 'fecha_registro', 'is_complete'
        ]
        read_only_fields = ['id', 'fecha_registro', 'is_complete'] # is_complete es una propiedad, no un campo editable

# Serializador para Cliente
class ClienteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Incluye los datos del usuario relacionado
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True) # Para crear/actualizar

    class Meta:
        model = Cliente
        fields = ['id', 'user', 'user_id', 'telefono']
        read_only_fields = ['id']

# Serializador para Direccion
class DireccionSerializer(serializers.ModelSerializer):
    cliente_id = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all(), source='cliente', write_only=True) # Para crear/actualizar vinculando un Cliente existente

    class Meta:
        model = Direccion
        fields = ['id', 'cliente', 'cliente_id', 'etiqueta', 'direccion', 'latitud', 'longitud', 'validada']
        read_only_fields = ['id']
        extra_kwargs = {
            'cliente': {'read_only': True} # Para evitar que el objeto Cliente completo se muestre en la salida
        }