# tiendas/serializers.py
from rest_framework import serializers
from .models import Tienda, RadioEnvio
from usuarios.serializers import PerfilVendedorSerializer # Importamos el serializador de PerfilVendedor
from usuarios.models import PerfilVendedor

# Serializador para RadioEnvio
class RadioEnvioSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all()) # Esta línea ya la agregaste y corregimos el KeyError con ella

    class Meta:
        model = RadioEnvio
        fields = ['id', 'tienda', 'distancia_max_km', 'costo_envio', 'envio_gratis'] # Y esta línea incluye 'tienda'
        read_only_fields = ['id']

# Serializador para Tienda
class TiendaSerializer(serializers.ModelSerializer):
    vendedor = PerfilVendedorSerializer(read_only=True)
    # Campo para poder enviar el ID del vendedor al crear/actualizar la tienda
    vendedor_id = serializers.PrimaryKeyRelatedField(queryset=PerfilVendedor.objects.all(), source='vendedor', write_only=True) # <-- ¡CORREGIDO!

    radios_envio = RadioEnvioSerializer(many=True, read_only=True)

    class Meta:
        model = Tienda
        fields = [
            'id', 'nombre', 'slug', 'descripcion', 'direccion', 'latitud', 'longitud',
            'telefono', 'email', 'url', 'horario_atencion', 'logo', 'fecha_creacion',
            'activo', 'vendedor', 'vendedor_id', 'radios_envio'
        ]
        read_only_fields = ['id', 'slug', 'fecha_creacion']
        
        
        
        