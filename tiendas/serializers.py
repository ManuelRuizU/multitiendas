# tiendas/serializers.py
from rest_framework import serializers
from .models import Tienda, RadioEnvio
from usuarios.serializers import PerfilVendedorSerializer # Importamos el serializador de PerfilVendedor

# Serializador para RadioEnvio (se usará como anidado en TiendaSerializer)
class RadioEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadioEnvio
        fields = ['id', 'distancia_max_km', 'costo_envio']
        read_only_fields = ['id']

# Serializador para Tienda
class TiendaSerializer(serializers.ModelSerializer):
    # Incluimos el serializador de PerfilVendedor si quieres ver los detalles del vendedor
    vendedor = PerfilVendedorSerializer(read_only=True) 
    # Campo para poder enviar el ID del vendedor al crear/actualizar la tienda
    vendedor_id = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all(), source='vendedor', write_only=True) # O PerfilVendedor.objects.all()

    radios_envio = RadioEnvioSerializer(many=True, read_only=True) # Muestra los radios de envío anidados, solo lectura

    class Meta:
        model = Tienda
        fields = [
            'id', 'nombre', 'slug', 'descripcion', 'direccion', 'latitud', 'longitud',
            'telefono', 'email', 'url', 'horario_atencion', 'logo', 'fecha_creacion',
            'activo', 'vendedor', 'vendedor_id', 'radios_envio'
        ]
        read_only_fields = ['id', 'slug', 'fecha_creacion']