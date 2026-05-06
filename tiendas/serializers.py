# tiendas/serializers.py
from rest_framework import serializers
from .models import Tienda, RadioEnvio
# No necesitamos importar PerfilVendedorSerializer ni PerfilVendedor aquí
# si solo mostramos el username del vendedor o si la asignación la hace la vista.

# Serializador para RadioEnvio
class RadioEnvioSerializer(serializers.ModelSerializer):
    # Permite enviar el ID de la tienda al crear/actualizar
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    # Campo de solo lectura para mostrar el nombre de la tienda en las respuestas GET
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')

    class Meta:
        model = RadioEnvio
        fields = ['id', 'tienda', 'tienda_nombre', 'distancia_max_km', 'costo_envio', 'envio_gratis']
        read_only_fields = ['id', 'tienda_nombre'] # 'id' y 'tienda_nombre' son de solo lectura

# Serializador para Tienda
class TiendaSerializer(serializers.ModelSerializer):
    # Campo de solo lectura para mostrar el username del vendedor en las respuestas GET
    # Este campo es solo para la salida (GET), no para la entrada (POST/PUT).
    vendedor_username = serializers.ReadOnlyField(source='vendedor.user.username')

    # Serializador anidado para mostrar los radios de envío de la tienda
    # Es de solo lectura, lo que significa que no se espera en la entrada al crear/actualizar la tienda.
    radios_envio = RadioEnvioSerializer(many=True, read_only=True)

    class Meta:
        model = Tienda
        fields = [
            'id', 'nombre', 'slug', 'descripcion', 'direccion', 'latitud', 'longitud',
            'telefono', 'email', 'url', 'horario_atencion', 'logo', 'fecha_creacion',
            'activo', 
            'vendedor_username', # Incluido en los campos para la salida de la API
            'radios_envio'
        ]
        # --- ¡CAMBIOS CLAVE AQUÍ! ---
        # 'vendedor' (el campo ForeignKey real en el modelo) debe ser de solo lectura.
        # Esto le dice al serializador que no espere 'vendedor' en la entrada (POST/PUT).
        # La vista (perform_create) se encargará de asignarlo.
        # 'vendedor_username' es un campo derivado, por lo tanto, solo lectura.
        read_only_fields = ['id', 'slug', 'fecha_creacion', 'vendedor', 'vendedor_username'] 


