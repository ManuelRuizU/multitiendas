# usuarios/serializers.py
from rest_framework_simplejwt.tokens import RefreshToken # Agrega esta importación

# ... (tus otras importaciones se mantienen)

class SellerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    # Campo para devolver tokens tras el registro exitoso
    tokens = serializers.SerializerMethodField(read_only=True)

    # (tus campos de teléfono, rut, etc., se mantienen igual)
    # ...

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2', 'first_name', 'last_name',
            'telefono_vendedor', 'rut', 'razon_social', 'giro', 'direccion_fiscal',
            'calle', 'numero', 'comuna', 'ciudad', 'tokens' # Agrega tokens aquí
        ]

    def get_tokens(self, user):
        """Genera tokens JWT automáticamente al registrarse."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        if SellerProfile.objects.filter(rut=data['rut']).exists():
            raise serializers.ValidationError({"rut": "El RUT ya está en uso."})
        return data

    def create(self, validated_data):
        # Limpieza de datos
        validated_data.pop('password2')
        direccion_data = {
            'calle': validated_data.pop('calle'),
            'numero': validated_data.pop('numero'),
            'comuna': validated_data.pop('comuna'),
            'ciudad': validated_data.pop('ciudad'),
        }
        
        seller_profile_data = {
            'telefono': validated_data.pop('telefono_vendedor'),
            'rut': validated_data.pop('rut'),
            'razon_social': validated_data.pop('razon_social'),
            'giro': validated_data.pop('giro'),
            'direccion_fiscal': validated_data.pop('direccion_fiscal'),
        }

        with transaction.atomic():
            # Creación del CustomUser
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
            )
            
            # Creación del Perfil de Vendedor
            SellerProfile.objects.create(user=user, **seller_profile_data)
            
            # Creación del Cliente (Importante para el flujo de pedidos)
            cliente = Cliente.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                telefono=seller_profile_data['telefono']
            )
            
            # Creación de la Dirección
            Direccion.objects.create(
                cliente=cliente,
                principal=True,
                etiqueta="Tienda Principal",
                **direccion_data
            )
            
            return user
        