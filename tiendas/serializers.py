# tiendas/serializers.py
from rest_framework import serializers
from .models import Tienda, RadioEnvio, CuadranteEnvio


# ------------------------------------------------------------------
# 1. RADIO DE ENVÍO
# ------------------------------------------------------------------
class RadioEnvioSerializer(serializers.ModelSerializer):
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')

    class Meta:
        model = RadioEnvio
        fields = [
            'id', 'tienda', 'tienda_nombre',
            'distancia_max_km', 'costo_envio', 'envio_gratis'
        ]
        read_only_fields = ['id', 'tienda_nombre']


# ------------------------------------------------------------------
# 2. CUADRANTE DE ENVÍO
# Dos versiones:
#   - CuadranteEnvioSerializer: completo, para el panel del vendedor
#   - CuadranteEnvioPublicoSerializer: sin polígono, para el público
# ------------------------------------------------------------------
class CuadranteEnvioSerializer(serializers.ModelSerializer):
    """Serializer completo — solo para el panel del vendedor."""
    class Meta:
        model = CuadranteEnvio
        fields = [
            'id', 'tienda', 'nombre', 'descripcion',
            'poligono', 'costo_envio', 'envio_gratis', 'activo',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


class CuadranteEnvioPublicoSerializer(serializers.ModelSerializer):
    """Serializer público — sin polígono para no exponer la geometría."""
    class Meta:
        model = CuadranteEnvio
        fields = ['id', 'nombre', 'costo_envio', 'envio_gratis', 'activo']
        read_only_fields = fields


# ------------------------------------------------------------------
# 3. TIENDA
# Dos versiones:
#   - TiendaPublicaSerializer: solo datos públicos, sin datos sensibles
#   - TiendaSerializer: completo, para el panel del vendedor
# ------------------------------------------------------------------
class TiendaPublicaSerializer(serializers.ModelSerializer):
    """
    Serializer público — para que los clientes vean las tiendas.
    No expone datos bancarios, tokens de Loyverse ni datos internos.
    """
    vendedor_username = serializers.ReadOnlyField(
        source='propietario_perfil.user.username'
    )
    metodos_pago = serializers.ReadOnlyField(source='metodos_pago_activos')
    whatsapp_url = serializers.ReadOnlyField(
        source='propietario_perfil.whatsapp_url'
    )
    radios_envio = RadioEnvioSerializer(many=True, read_only=True)
    cuadrantes   = CuadranteEnvioPublicoSerializer(many=True, read_only=True)
    esta_abierto = serializers.ReadOnlyField()

    class Meta:
        model = Tienda
        fields = [
            'id', 'nombre', 'slug', 'tipo_negocio', 'descripcion',
            'direccion', 'latitud', 'longitud',
            'telefono', 'email', 'url', 'horario_atencion', 'logo', 'banner',
            'activo', 'fecha_creacion',
            'acepta_efectivo', 'acepta_transferencia', 'acepta_link_pago',
            'metodos_pago', 'whatsapp_url',
            'vendedor_username',
            'radios_envio', 'cuadrantes',
            # Horario
            'esta_abierto', 'acepta_pedidos_programados',
            'hora_apertura', 'hora_cierre',
            'abre_lunes', 'abre_martes', 'abre_miercoles', 'abre_jueves',
            'abre_viernes', 'abre_sabado', 'abre_domingo',
        ]
        read_only_fields = fields


class TiendaSerializer(serializers.ModelSerializer):
    """
    Serializer completo — para el panel del vendedor.
    Incluye datos bancarios, configuración de Loyverse y repartidores.
    """
    vendedor_username = serializers.ReadOnlyField(
        source='propietario_perfil.user.username'
    )
    metodos_pago = serializers.ReadOnlyField(source='metodos_pago_activos')
    loyverse_configurado = serializers.ReadOnlyField()
    stock_ilimitado_default = serializers.ReadOnlyField()
    whatsapp_vendedor = serializers.ReadOnlyField(
        source='propietario_perfil.whatsapp'
    )
    whatsapp_url = serializers.ReadOnlyField(
        source='propietario_perfil.whatsapp_url'
    )
    radios_envio = RadioEnvioSerializer(many=True, read_only=True)
    cuadrantes = CuadranteEnvioSerializer(many=True, read_only=True)

    class Meta:
        model = Tienda
        fields = [
            # Información general
            'id', 'nombre', 'slug', 'tipo_negocio', 'descripcion',
            'activo', 'fecha_creacion',

            # Ubicación
            'direccion', 'latitud', 'longitud',

            # Contacto
            'telefono', 'email', 'url', 'horario_atencion', 'logo', 'banner',

            # Horario estructurado
            'esta_abierto', 'acepta_pedidos_programados',
            'hora_apertura', 'hora_cierre',
            'abre_lunes', 'abre_martes', 'abre_miercoles', 'abre_jueves',
            'abre_viernes', 'abre_sabado', 'abre_domingo',

            # Métodos de pago
            'acepta_efectivo', 'acepta_transferencia', 'acepta_link_pago',
            'banco', 'tipo_cuenta', 'numero_cuenta',
            'titular_cuenta', 'rut_titular', 'email_transferencia',
            'link_pago_url', 'instrucciones_link_pago',
            'metodos_pago',

            # Repartidores
            'modo_asignacion_default',

            # Loyverse
            'loyverse_activo', 'loyverse_token', 'loyverse_store_id',
            'loyverse_configurado',

            # Propiedades útiles
            'stock_ilimitado_default',
            'whatsapp_vendedor', 'whatsapp_url',
            'vendedor_username',

            # Relaciones
            'radios_envio', 'cuadrantes',
        ]
        read_only_fields = [
            'id', 'slug', 'fecha_creacion',
            'propietario_perfil', 'vendedor_username',
            'metodos_pago', 'loyverse_configurado',
            'stock_ilimitado_default',
            'whatsapp_vendedor', 'whatsapp_url',
            'esta_abierto',
        ]
        extra_kwargs = {
            'loyverse_token': {'write_only': True},
        }

    def validate(self, data):
        """
        Validaciones a nivel de serializer para devolver errores
        400 más descriptivos al frontend antes de llamar al modelo.
        """
        acepta_efectivo = data.get('acepta_efectivo', True)
        acepta_transferencia = data.get('acepta_transferencia', False)
        acepta_link_pago = data.get('acepta_link_pago', False)

        # Al menos un método de pago
        if not any([acepta_efectivo, acepta_transferencia, acepta_link_pago]):
            raise serializers.ValidationError(
                "Debes activar al menos un método de pago."
            )

        # Datos bancarios obligatorios si acepta transferencia
        if acepta_transferencia:
            campos = ['banco', 'tipo_cuenta', 'numero_cuenta',
                      'titular_cuenta', 'rut_titular', 'email_transferencia']
            faltantes = [c for c in campos if not data.get(c)]
            if faltantes:
                raise serializers.ValidationError(
                    f"Faltan datos bancarios: {', '.join(faltantes)}"
                )

        # URL obligatoria si acepta link de pago
        if acepta_link_pago and not data.get('link_pago_url'):
            raise serializers.ValidationError(
                "Debes ingresar la URL del link de pago."
            )

        return data