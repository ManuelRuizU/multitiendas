# tiendas/serializers.py
from rest_framework import serializers
from .models import Tienda, RadioEnvio, CuadranteEnvio

# 1. SERIALIZADOR PARA RADIO ENVIO
class RadioEnvioSerializer(serializers.ModelSerializer):
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')

    class Meta:
        model = RadioEnvio
        fields = ['id', 'tienda', 'tienda_nombre', 'distancia_max_km', 'costo_envio', 'envio_gratis']
        read_only_fields = ['id', 'tienda_nombre']

# 2. SERIALIZADOR PARA CUADRANTE ENVIO (Añadido)
class CuadranteEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuadranteEnvio
        fields = ['id', 'tienda', 'nombre', 'descripcion', 'poligono', 'costo_envio', 'envio_gratis', 'activo']
        read_only_fields = ['id']

# 3. SERIALIZADOR PARA TIENDA
class TiendaSerializer(serializers.ModelSerializer):
    # Ajustado al nombre real del campo en tu models.py: 'propietario_perfil'
    vendedor_username = serializers.ReadOnlyField(source='propietario_perfil.user.username')
    
    # Serializadores anidados
    radios_envio = RadioEnvioSerializer(many=True, read_only=True)
    cuadrantes = CuadranteEnvioSerializer(many=True, read_only=True)

    class Meta:
        model = Tienda
        fields = [
            'id', 'nombre', 'slug', 'tipo_negocio', 'descripcion', 
            'direccion', 'latitud', 'longitud', 'telefono', 'email', 
            'url', 'horario_atencion', 'logo', 'fecha_creacion', 'activo',
            
            # Métodos de Pago (Necesarios para el full_clean del modelo)
            'acepta_efectivo', 'acepta_transferencia', 'acepta_link_pago',
            
            # Datos Bancarios
            'banco', 'tipo_cuenta', 'numero_cuenta', 'titular_cuenta', 
            'rut_titular', 'email_transferencia',
            
            # Otros
            'vendedor_username', 'radios_envio', 'cuadrantes'
        ]
        # 'propietario_perfil' es el FK, lo ponemos como read_only para asignarlo en la vista
        read_only_fields = ['id', 'slug', 'fecha_creacion', 'propietario_perfil', 'vendedor_username']

    def validate(self, data):
        """
        Opcional: Puedes replicar aquí algunas validaciones del clean() 
        del modelo para devolver errores 400 más limpios al frontend.
        """
        return data
