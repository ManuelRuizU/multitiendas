# usuarios/serializers.py
from rest_framework import serializers 
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion # Asegúrate de que estos modelos existan

# --- MODIFICACIÓN AQUÍ ---
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        # Asegúrate de que las contraseñas coincidan
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data

    def create(self, validated_data):
        # Extrae y elimina password2 antes de crear el usuario
        validated_data.pop('password2')
        # Crea el usuario y hashea la contraseña
        user = User.objects.create_user(**validated_data)
        return user
# --- FIN DE LA MODIFICACIÓN ---


# Serializador para el modelo User (si lo quieres solo para lectura en otros contextos, puedes mantener el original)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['username'] # Generalmente no permites cambiar el username por API una vez creado

# Serializador para PerfilVendedor
class PerfilVendedorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Incluye los datos del usuario relacionado, solo para lectura
    # Cambia a ManyToOneRel para que el campo user_id apunte a un User
    # Asegúrate de que el queryset de User.objects.all() sea correcto
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)

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
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all(), source='cliente', write_only=True) # Renombrado a 'cliente' para ser consistente

    class Meta:
        model = Direccion
        # Se necesita un campo para mostrar el ID del cliente si cliente es write_only,
        # o se asume que el ViewSet manejará la asignación desde el usuario autenticado.
        fields = ['id', 'cliente', 'etiqueta', 'direccion', 'latitud', 'longitud', 'validada']
        read_only_fields = ['id']
        extra_kwargs = {
            'cliente': {'read_only': True} # Si lo haces write_only=True arriba, esto es redundante
        }
        