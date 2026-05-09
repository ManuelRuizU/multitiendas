# usuarios/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser as User, BuyerProfile, SellerProfile, Cliente, Direccion


# ------------------------------------------------------------------
# UTILIDAD: Generar tokens JWT
# ------------------------------------------------------------------
def get_tokens_for_user(user):
    """
    Genera tokens JWT para un usuario.
    Se usa en los serializers de registro para devolver tokens
    automáticamente al completar el registro.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ------------------------------------------------------------------
# 1. SERIALIZER DE REGISTRO DE CLIENTE
# Registro básico — cualquier visitante puede registrarse.
# Crea: CustomUser (is_cliente=True) + BuyerProfile + Cliente
# ------------------------------------------------------------------
class ClienteRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    # Campos opcionales del perfil
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'telefono',
            'tokens',
        ]

    def get_tokens(self, obj):
        return get_tokens_for_user(obj)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Este email ya está registrado."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        telefono = validated_data.pop('telefono', None)

        with transaction.atomic():
            # Crear usuario (is_cliente=True por defecto)
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
            )

            # BuyerProfile se crea automáticamente via señal
            # pero actualizamos el teléfono si se proporcionó
            if telefono and hasattr(user, 'buyer_profile'):
                user.buyer_profile.telefono = telefono
                user.buyer_profile.save(update_fields=['telefono'])

            # Crear Cliente para el flujo de pedidos
            Cliente.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                telefono=telefono,
            )

            return user


# ------------------------------------------------------------------
# 2. SERIALIZER DE REGISTRO DE VENDEDOR
# El usuario completa el registro como emprendedor.
# Crea: CustomUser + BuyerProfile + SellerProfile + Cliente + Direccion
# El SellerProfile.save() activa is_vendedor=True automáticamente.
# ------------------------------------------------------------------
class SellerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    # Campos del SellerProfile
    telefono_vendedor = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)
    whatsapp = serializers.CharField(max_length=15, required=True, write_only=True)
    rut = serializers.CharField(max_length=12, required=True, write_only=True)
    razon_social = serializers.CharField(max_length=150, required=True, write_only=True)
    giro = serializers.CharField(max_length=150, required=True, write_only=True)
    direccion_fiscal = serializers.CharField(max_length=255, required=True, write_only=True)

    # Dirección de la tienda (se crea como Cliente.Direccion)
    calle = serializers.CharField(max_length=255, required=True, write_only=True)
    numero = serializers.CharField(max_length=20, required=True, write_only=True)
    comuna = serializers.CharField(max_length=100, required=True, write_only=True)
    ciudad = serializers.CharField(max_length=100, required=True, write_only=True)
    region = serializers.CharField(max_length=100, required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            # Datos del usuario
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name',
            # Datos del perfil de vendedor
            'telefono_vendedor', 'whatsapp', 'rut',
            'razon_social', 'giro', 'direccion_fiscal',
            # Dirección
            'calle', 'numero', 'comuna', 'ciudad', 'region',
            # Respuesta
            'tokens',
        ]

    def get_tokens(self, obj):
        return get_tokens_for_user(obj)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Este email ya está registrado."}
            )
        if SellerProfile.objects.filter(rut=data['rut']).exists():
            raise serializers.ValidationError(
                {"rut": "Este RUT ya está registrado en la plataforma."}
            )
        # Validar formato WhatsApp
        import re
        if not re.match(r'^\+56[2-9]\d{8}$', data['whatsapp']):
            raise serializers.ValidationError(
                {"whatsapp": "Formato inválido. Usa +56912345678"}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('password2')

        # Extraer datos del perfil
        seller_data = {
            'telefono': validated_data.pop('telefono_vendedor', None),
            'whatsapp': validated_data.pop('whatsapp'),
            'rut': validated_data.pop('rut'),
            'razon_social': validated_data.pop('razon_social'),
            'giro': validated_data.pop('giro'),
            'direccion_fiscal': validated_data.pop('direccion_fiscal'),
        }

        # Extraer datos de dirección
        direccion_data = {
            'calle': validated_data.pop('calle'),
            'numero': validated_data.pop('numero'),
            'comuna': validated_data.pop('comuna'),
            'ciudad': validated_data.pop('ciudad'),
            'region': validated_data.pop('region'),
        }

        with transaction.atomic():
            # Crear usuario
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
            )

            # Crear SellerProfile → activa is_vendedor=True automáticamente
            SellerProfile.objects.create(user=user, **seller_data)

            # Crear Cliente para el flujo de pedidos
            cliente = Cliente.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                telefono=seller_data.get('telefono'),
            )

            # Crear Dirección principal del vendedor
            Direccion.objects.create(
                cliente=cliente,
                principal=True,
                etiqueta="Tienda Principal",
                **direccion_data
            )

            return user


# ------------------------------------------------------------------
# 3. SERIALIZER DE REGISTRO DE REPARTIDOR
# El usuario completa el registro como repartidor.
# Crea: CustomUser + BuyerProfile + Repartidor
# Repartidor.save() activa is_repartidor=True automáticamente.
# ------------------------------------------------------------------
class RepartidorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    # Campos del Repartidor
    telefono = serializers.CharField(max_length=20, required=True, write_only=True)
    vehiculo = serializers.ChoiceField(
        choices=['BICICLETA', 'MOTO', 'AUTO', 'FURGON', 'A_PIE', 'OTRO'],
        required=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name',
            'telefono', 'vehiculo',
            'tokens',
        ]

    def get_tokens(self, obj):
        return get_tokens_for_user(obj)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Este email ya está registrado."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('password2')

        repartidor_data = {
            'telefono': validated_data.pop('telefono'),
            'vehiculo': validated_data.pop('vehiculo'),
        }

        with transaction.atomic():
            # Crear usuario
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
            )

            # Importar aquí para evitar importación circular
            from repartidores.models import Repartidor

            # Crear Repartidor → activa is_repartidor=True automáticamente
            Repartidor.objects.create(user=user, **repartidor_data)

            # Crear Cliente para que el repartidor también pueda comprar
            Cliente.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                telefono=repartidor_data['telefono'],
            )

            return user


# ------------------------------------------------------------------
# 4. SERIALIZER DE PERFIL DE USUARIO
# Para mostrar y editar los datos del usuario autenticado.
# ------------------------------------------------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField(read_only=True)
    tiene_seller_profile = serializers.SerializerMethodField(read_only=True)
    tiene_repartidor_profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_cliente', 'is_vendedor', 'is_repartidor',
            'roles',
            'tiene_seller_profile',
            'tiene_repartidor_profile',
        ]
        read_only_fields = [
            'id', 'is_cliente', 'is_vendedor', 'is_repartidor',
            'roles', 'tiene_seller_profile', 'tiene_repartidor_profile',
        ]

    def get_roles(self, obj):
        return obj.roles_activos

    def get_tiene_seller_profile(self, obj):
        return hasattr(obj, 'seller_profile')

    def get_tiene_repartidor_profile(self, obj):
        return hasattr(obj, 'repartidor_profile')


# ------------------------------------------------------------------
# 5. SERIALIZER DE DIRECCIÓN
# ------------------------------------------------------------------
class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = [
            'id', 'etiqueta', 'calle', 'numero',
            'tipo_propiedad', 'departamento', 'block', 'nombre_condominio',
            'comuna', 'ciudad', 'region', 'codigo_postal',
            'latitud', 'longitud', 'validada',
            'tipo_direccion', 'principal',
        ]
        read_only_fields = ['validada']


# ------------------------------------------------------------------
# 6. SERIALIZER DE USUARIO (lectura)
# Para mostrar datos del usuario en el token y perfil.
# ------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_cliente', 'is_vendedor', 'is_repartidor',
            'roles',
        ]
        read_only_fields = ['id', 'is_cliente', 'is_vendedor', 'is_repartidor']

    def get_roles(self, obj):
        return obj.roles_activos


# ------------------------------------------------------------------
# 7. SERIALIZER DE BUYERPROFILE
# ------------------------------------------------------------------
class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = ['user', 'telefono']
        read_only_fields = ['user']


# ------------------------------------------------------------------
# 8. SERIALIZER DE SELLERPROFILE
# ------------------------------------------------------------------
class SellerProfileSerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.ReadOnlyField()
    perfil_completo = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = [
            'user', 'telefono', 'whatsapp', 'whatsapp_url',
            'rut', 'razon_social', 'giro', 'direccion_fiscal',
            'fecha_registro', 'perfil_completo',
        ]
        read_only_fields = ['user', 'fecha_registro', 'whatsapp_url']

    def get_perfil_completo(self, obj):
        return obj.is_complete()


# ------------------------------------------------------------------
# 9. SERIALIZER DE CLIENTE
# ------------------------------------------------------------------
class ClienteSerializer(serializers.ModelSerializer):
    direcciones = DireccionSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'user', 'first_name', 'last_name',
            'email', 'telefono', 'is_guest', 'guest_uuid',
            'direcciones',
        ]
        read_only_fields = ['user', 'is_guest', 'guest_uuid']


# ------------------------------------------------------------------
# 10. SERIALIZER DE CAMBIO DE CONTRASEÑA
# ------------------------------------------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas nuevas no coinciden."}
            )
        return data
    
    