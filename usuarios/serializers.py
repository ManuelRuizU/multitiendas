# usuarios/serializers.py
# Modificado: 23/8/2025

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
import logging

# Importar los modelos locales y la función de utilidad
from .models import BuyerProfile, SellerProfile, Cliente, Direccion, UserType
from .utils import get_geocoding_from_address

# Configurar logging para depuración
logger = logging.getLogger(__name__)

# Obtener el modelo de usuario de forma segura
User = get_user_model()

# ------------------------------------------------------------------
# 1. SERIALIZADOR DE USUARIO BÁSICO
# ------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    """
    Serializador básico para representar un usuario.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']
        read_only_fields = ['id', 'user_type']

# ------------------------------------------------------------------
# 2. SERIALIZADOR DE REGISTRO DE COMPRADOR
# ------------------------------------------------------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios de tipo comprador.
    Crea un objeto User, un Cliente y una Direccion.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    cliente_id = serializers.IntegerField(read_only=True)
    
    # Campos de dirección y teléfono para la entrada de datos
    calle = serializers.CharField(required=True, write_only=True)
    numero = serializers.CharField(required=True, write_only=True)
    comuna = serializers.CharField(required=True, write_only=True)
    ciudad = serializers.CharField(required=True, write_only=True)
    telefono = serializers.CharField(max_length=20, required=True, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'cliente_id', 'calle', 'numero', 'comuna', 'ciudad', 'telefono')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        # Extrae los datos de la dirección antes de la creación del usuario
        validated_data.pop('password2')
        calle = validated_data.pop('calle')
        numero = validated_data.pop('numero')
        comuna = validated_data.pop('comuna')
        ciudad = validated_data.pop('ciudad')
        telefono = validated_data.pop('telefono')
        
        # Realiza la geocodificación
        latitud = None
        longitud = None
        validada = False
        try:
            latitud, longitud = get_geocoding_from_address(calle, numero, comuna, ciudad)
            if latitud is not None and longitud is not None:
                validada = True
            else:
                logger.warning(f"Geocodificación falló para {calle} {numero}, {comuna}, {ciudad}. Dirección registrada sin coordenadas.")
        except Exception as e:
            logger.error(f"Error en geocodificación para {calle} {numero}, {comuna}, {ciudad}: {str(e)}")

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                user_type=UserType.BUYER,
                is_active=True  # Añadido explícitamente
            )
            cliente = Cliente.objects.create(
                user=user,
                is_guest=False,
                guest_uuid=None,
                first_name=validated_data.get('first_name'),
                last_name=validated_data.get('last_name'),
                email=validated_data.get('email'),
                telefono=telefono
            )
            Direccion.objects.create(
                cliente=cliente,
                calle=calle,
                numero=numero,
                comuna=comuna,
                ciudad=ciudad,
                latitud=latitud,
                longitud=longitud,
                validada=validada,
                principal=True
            )
            
            # Eliminado: user.cliente_id = cliente.id
            # La relación ya está manejada por cliente_data
            user.save()
            return user

    def to_representation(self, instance):
        # Obtener la representación básica del usuario
        representation = super().to_representation(instance)
        
        # Refrescar el objeto usuario para asegurar que las relaciones estén disponibles
        instance.refresh_from_db()
        
        # Añadir campos adicionales desde Cliente y Direccion
        try:
            cliente = getattr(instance, 'cliente_data', None)
            if cliente:
                representation['cliente_id'] = cliente.id  # Añadido manualmente
                representation['telefono'] = cliente.telefono
                direccion = cliente.direcciones.filter(principal=True).first()
                if direccion:
                    representation['calle'] = direccion.calle
                    representation['numero'] = direccion.numero
                    representation['comuna'] = direccion.comuna
                    representation['ciudad'] = direccion.ciudad
                else:
                    representation['calle'] = None
                    representation['numero'] = None
                    representation['comuna'] = None
                    representation['ciudad'] = None
            else:
                representation['cliente_id'] = None
                representation['telefono'] = None
                representation['calle'] = None
                representation['numero'] = None
                representation['comuna'] = None
                representation['ciudad'] = None
        except Exception as e:
            logger.error(f"Error en to_representation (UserRegistrationSerializer): {str(e)}")
            representation['cliente_id'] = None
            representation['telefono'] = None
            representation['calle'] = None
            representation['numero'] = None
            representation['comuna'] = None
            representation['ciudad'] = None
            
        return representation

# ------------------------------------------------------------------
# 3. SERIALIZADOR DE REGISTRO DE VENDEDOR
# ------------------------------------------------------------------
class SellerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios de tipo vendedor.
    Crea un objeto User, un Cliente y un SellerProfile con sus datos.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    # Campos del perfil de vendedor anidados para la entrada de datos
    telefono_vendedor = serializers.CharField(max_length=20, required=True, write_only=True)
    rut = serializers.CharField(max_length=12, required=True, write_only=True)
    razon_social = serializers.CharField(max_length=150, required=True, write_only=True)
    giro = serializers.CharField(max_length=150, required=True, write_only=True)
    direccion_fiscal = serializers.CharField(max_length=255, required=True, write_only=True)

    # Campos de dirección de la tienda para la entrada de datos
    calle = serializers.CharField(required=True, write_only=True)
    numero = serializers.CharField(required=True, write_only=True)
    comuna = serializers.CharField(required=True, write_only=True)
    ciudad = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2', 'first_name', 'last_name',
            'telefono_vendedor', 'rut', 'razon_social', 'giro', 'direccion_fiscal',
            'calle', 'numero', 'comuna', 'ciudad'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        
        if SellerProfile.objects.filter(rut=data['rut']).exists():
            raise serializers.ValidationError({"rut": "El RUT ya está en uso."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        
        # 1. Extrae los datos de la dirección y el perfil del vendedor
        calle = validated_data.pop('calle')
        numero = validated_data.pop('numero')
        comuna = validated_data.pop('comuna')
        ciudad = validated_data.pop('ciudad')
        
        seller_profile_data = {
            'telefono': validated_data.pop('telefono_vendedor'),
            'rut': validated_data.pop('rut'),
            'razon_social': validated_data.pop('razon_social'),
            'giro': validated_data.pop('giro'),
            'direccion_fiscal': validated_data.pop('direccion_fiscal'),
        }

        # 2. Realiza la geocodificación
        latitud = None
        longitud = None
        validada = False
        try:
            latitud, longitud = get_geocoding_from_address(calle, numero, comuna, ciudad)
            if latitud is not None and longitud is not None:
                validada = True
            else:
                logger.warning(f"Geocodificación falló para {calle} {numero}, {comuna}, {ciudad}. Dirección registrada sin coordenadas.")
        except Exception as e:
            logger.error(f"Error en geocodificación para {calle} {numero}, {comuna}, {ciudad}: {str(e)}")

        with transaction.atomic():
            # 3. Crea el usuario y su perfil de vendedor
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                user_type=UserType.SELLER,
                is_active=True
            )
            SellerProfile.objects.create(user=user, **seller_profile_data)
            
            # 4. Crea el objeto Cliente asociado
            cliente = Cliente.objects.create(
                user=user,
                is_guest=False,
                guest_uuid=None,
                first_name=validated_data.get('first_name'),
                last_name=validated_data.get('last_name'),
                email=validated_data.get('email'),
                telefono=seller_profile_data.get('telefono')
            )
            
            # 5. Crea la dirección de la tienda del vendedor con las coordenadas obtenidas
            Direccion.objects.create(
                cliente=cliente,
                calle=calle,
                numero=numero,
                comuna=comuna,
                ciudad=ciudad,
                latitud=latitud,
                longitud=longitud,
                validada=validada,
                principal=True,
                etiqueta="Tienda Principal"
            )
            
            # Eliminado: user.cliente_id = cliente.id
            # La relación ya está manejada por cliente_data
            user.save()
            return user

    def to_representation(self, instance):
        # Obtener la representación básica del usuario
        representation = super().to_representation(instance)
        
        # Refrescar el objeto usuario para asegurar que las relaciones estén disponibles
        instance.refresh_from_db()
        
        # Añadir campos adicionales desde SellerProfile, Cliente y Direccion
        try:
            seller_profile = getattr(instance, 'seller_profile', None)
            cliente = getattr(instance, 'cliente_data', None)
            if seller_profile:
                representation['rut'] = seller_profile.rut
                representation['razon_social'] = seller_profile.razon_social
                representation['giro'] = seller_profile.giro
                representation['direccion_fiscal'] = seller_profile.direccion_fiscal
                representation['telefono_vendedor'] = seller_profile.telefono
            else:
                representation['rut'] = None
                representation['razon_social'] = None
                representation['giro'] = None
                representation['direccion_fiscal'] = None
                representation['telefono_vendedor'] = None
                
            if cliente:
                representation['cliente_id'] = cliente.id  # Añadido manualmente
                direccion = cliente.direcciones.filter(principal=True).first()
                if direccion:
                    representation['calle'] = direccion.calle
                    representation['numero'] = direccion.numero
                    representation['comuna'] = direccion.comuna
                    representation['ciudad'] = direccion.ciudad
                else:
                    representation['calle'] = None
                    representation['numero'] = None
                    representation['comuna'] = None
                    representation['ciudad'] = None
            else:
                representation['cliente_id'] = None
                representation['calle'] = None
                representation['numero'] = None
                representation['comuna'] = None
                representation['ciudad'] = None
        except Exception as e:
            logger.error(f"Error en to_representation (SellerRegistrationSerializer): {str(e)}")
            representation['rut'] = None
            representation['razon_social'] = None
            representation['giro'] = None
            representation['direccion_fiscal'] = None
            representation['telefono_vendedor'] = None
            representation['cliente_id'] = None
            representation['calle'] = None
            representation['numero'] = None
            representation['comuna'] = None
            representation['ciudad'] = None
            
        return representation

# ------------------------------------------------------------------
# 4. SERIALIZADOR DE PERFIL DE COMPRADOR
# ------------------------------------------------------------------
class BuyerProfileSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo BuyerProfile.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = BuyerProfile
        fields = '__all__'
        read_only_fields = ['user']

# ------------------------------------------------------------------
# 5. SERIALIZADOR DE PERFIL DE VENDEDOR
# ------------------------------------------------------------------
class SellerProfileSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo SellerProfile.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = SellerProfile
        fields = ['id', 'user', 'telefono', 'rut', 'razon_social', 'giro', 'direccion_fiscal', 'fecha_registro']
        read_only_fields = ['id', 'user', 'fecha_registro']

# ------------------------------------------------------------------
# 6. SERIALIZADOR DE CLIENTE
# ------------------------------------------------------------------
class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Cliente.
    """
    user_username = serializers.ReadOnlyField(source='user.username', allow_null=True)
    user_email = serializers.ReadOnlyField(source='user.email', allow_null=True)

    class Meta:
        model = Cliente
        fields = ['id', 'user_username', 'user_email', 'first_name', 'last_name', 'email', 'telefono', 'is_guest', 'guest_uuid']
        read_only_fields = ['id', 'is_guest', 'guest_uuid', 'user_username', 'user_email']

# ------------------------------------------------------------------
# 7. SERIALIZADOR DE DIRECCIÓN
# ------------------------------------------------------------------
class DireccionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Direccion.
    Soporta creación y actualización de direcciones con geocodificación opcional.
    """
    # Representación anidada del cliente para la respuesta
    cliente_info = ClienteSerializer(source='cliente', read_only=True)
    
    # Campo de solo escritura para el input de la API
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(), write_only=True
    )
    
    # Campo para la etiqueta, opcional
    etiqueta = serializers.CharField(required=False, allow_blank=True, max_length=150)

    # Campo para indicar si la dirección es la principal
    principal = serializers.BooleanField(required=False)

    class Meta:
        model = Direccion
        fields = [
            'id', 'cliente', 'cliente_info', 'etiqueta', 'calle', 'numero',
            'tipo_propiedad', 'departamento', 'block', 'nombre_condominio',
            'comuna', 'ciudad', 'region', 'codigo_postal', 'latitud', 'longitud',
            'validada', 'principal',
        ]
        read_only_fields = ['id', 'validada', 'cliente_info']

    def validate(self, attrs):
        """
        Valida que si se marca como principal, no haya otra dirección principal para el mismo cliente.
        """
        principal = attrs.get('principal', False)
        cliente = attrs.get('cliente')
        
        if principal and cliente:
            # Verificar si ya existe una dirección principal para este cliente
            existing_principal = Direccion.objects.filter(cliente=cliente, principal=True)
            if self.instance:  # En actualización, excluir la instancia actual
                existing_principal = existing_principal.exclude(id=self.instance.id)
            if existing_principal.exists():
                raise serializers.ValidationError({
                    "principal": "Ya existe una dirección principal para este cliente. Desmarca la otra primero."
                })
        
        return attrs

    def create(self, validated_data):
        """
        Crea una nueva dirección con geocodificación opcional.
        """
        calle = validated_data.get('calle')
        numero = validated_data.get('numero')
        comuna = validated_data.get('comuna')
        ciudad = validated_data.get('ciudad')
        
        # Realiza la geocodificación
        latitud = None
        longitud = None
        validada = False
        try:
            latitud, longitud = get_geocoding_from_address(calle, numero, comuna, ciudad)
            if latitud is not None and longitud is not None:
                validada = True
            else:
                logger.warning(f"Geocodificación falló para {calle} {numero}, {comuna}, {ciudad}. Dirección registrada sin coordenadas.")
        except Exception as e:
            logger.error(f"Error en geocodificación para {calle} {numero}, {comuna}, {ciudad}: {str(e)}")

        validated_data['latitud'] = latitud
        validated_data['longitud'] = longitud
        validated_data['validada'] = validada
        
        return Direccion.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Actualiza una dirección existente con geocodificación opcional si se cambian los campos de dirección.
        """
        # Verificar si los campos de dirección han cambiado
        calle = validated_data.get('calle', instance.calle)
        numero = validated_data.get('numero', instance.numero)
        comuna = validated_data.get('comuna', instance.comuna)
        ciudad = validated_data.get('ciudad', instance.ciudad)

        if (calle != instance.calle or numero != instance.numero or 
            comuna != instance.comuna or ciudad != instance.ciudad):
            # Realiza la geocodificación si la dirección cambió
            latitud = None
            longitud = None
            validada = False
            try:
                latitud, longitud = get_geocoding_from_address(calle, numero, comuna, ciudad)
                if latitud is not None and longitud is not None:
                    validada = True
                else:
                    logger.warning(f"Geocodificación falló para {calle} {numero}, {comuna}, {ciudad}. Dirección actualizada sin coordenadas.")
            except Exception as e:
                logger.error(f"Error en geocodificación para {calle} {numero}, {comuna}, {ciudad}: {str(e)}")
            
            validated_data['latitud'] = latitud
            validated_data['longitud'] = longitud
            validated_data['validada'] = validada

        return super().update(instance, validated_data)

# ------------------------------------------------------------------
# 8. SERIALIZADOR PARA CAMBIO DE CONTRASEÑA
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
            raise serializers.ValidationError({"new_password": "Las nuevas contraseñas no coinciden."})
        return attrs