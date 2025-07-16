# usuarios/serializers.py
from rest_framework import serializers 
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion # Asegúrate de que estos modelos existan

# --- SERIALIZADOR DE REGISTRO DE NUEVOS USUARIOS (SIN CAMBIOS) ---
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
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Este nombre de usuario ya está en uso."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Este correo electrónico ya está registrado."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

# --- SERIALIZADOR BÁSICO PARA EL MODELO USER (SIN CAMBIOS) ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['username', 'email']

# --- SERIALIZADOR PARA PERFILVENDEDOR (AJUSTADO: user_id es opcional) ---
class PerfilVendedorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) 
    # Hacemos user_id opcional (required=False) y permitimos nulos (allow_null=True)
    # Esto es para permitir que la vista asigne automáticamente el usuario autenticado.
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True, 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = PerfilVendedor
        fields = [
            'id', 'user', 'user_id', 'telefono', 'rut', 'razon_social',
            'giro', 'direccion_fiscal', 'fecha_registro', 'is_complete'
        ]
        read_only_fields = ['id', 'fecha_registro', 'is_complete']

# --- SERIALIZADOR PARA CLIENTE (ADAPTADO PARA INVITADOS) ---
class ClienteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) 
    # user_id es opcional y puede ser nulo, permitiendo clientes sin User vinculado.
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True, 
        required=False, 
        allow_null=True
    )
    
    # Nuevos campos del modelo Cliente para clientes invitados
    # Son 'required=False' en el serializador porque un cliente REGISTRADO no necesita enviarlos
    # (su info viene de User), pero serán validados en el `validate` para INVITADOS.
    email = serializers.EmailField(required=False, allow_blank=True)
    nombre_completo = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = Cliente
        # Incluye los nuevos campos y 'is_guest' que ahora está en el modelo
        fields = ['id', 'user', 'user_id', 'telefono', 'email', 'nombre_completo', 'is_guest'] 
        read_only_fields = ['id', 'is_guest'] # 'is_guest' es calculado por el modelo y solo para lectura

    def validate(self, data):
        if not data.get('user') and not data.get('user_id'): 
            if not data.get('email'):
                raise serializers.ValidationError({"email": "El email es obligatorio para clientes invitados."})
            if not data.get('nombre_completo'):
                raise serializers.ValidationError({"nombre_completo": "El nombre completo es obligatorio para clientes invitados."})
            
        return data

    def create(self, validated_data):
        if 'user' in validated_data and validated_data['user'] is None:
            validated_data.pop('user')

        if 'user_id' in validated_data and validated_data['user_id'] is None:
            validated_data.pop('user_id')

        return super().create(validated_data)


# --- SERIALIZADOR PARA DIRECCION (¡CORREGIDO!) ---
class DireccionSerializer(serializers.ModelSerializer):
    # 'cliente': Campo de escritura para recibir el ID del cliente al que pertenece la dirección.
    # Es REQUERIDO aquí, o la vista debe asignarlo. Asumo que lo pasarás en el POST.
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all()) # <-- 'write_only=True' y 'required=True' por defecto
    
    # 'cliente_id': Campo de lectura para mostrar el ID del cliente asociado a la dirección.
    cliente_id = serializers.IntegerField(source='cliente.id', read_only=True)

    class Meta:
        model = Direccion
        fields = [
            'id', 'cliente_id', 'cliente', 'etiqueta',
            'calle', 'numero', 'departamento', 'comuna', 'ciudad', 'region', 'codigo_postal',
            'tipo_direccion', 'principal', 'latitud', 'longitud', 'validada' # <-- ¡Campos de dirección añadidos!
        ]
        read_only_fields = ['id', 'cliente_id']

    # Opcional: Si quieres que 'cliente' se asigne automáticamente en la vista,
    # el campo 'cliente' en el serializador puede ser required=False y allow_null=True
    # Y la vista (perform_create) buscaría el cliente del usuario autenticado.
    # Pero por ahora, asumo que lo pasarás en el body.
    
    