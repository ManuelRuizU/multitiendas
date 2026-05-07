# tiendas/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Tienda, RadioEnvio, CuadranteEnvio


# ------------------------------------------------------------------
# INLINES
# ------------------------------------------------------------------
class RadioEnvioInline(admin.TabularInline):
    model = RadioEnvio
    extra = 1
    fields = ('distancia_max_km', 'costo_envio', 'envio_gratis')


class CuadranteEnvioInline(admin.TabularInline):
    model = CuadranteEnvio
    extra = 0
    fields = ('nombre', 'descripcion', 'costo_envio', 'envio_gratis', 'activo')
    readonly_fields = ('fecha_creacion',)


# ------------------------------------------------------------------
# TIENDA
# ------------------------------------------------------------------
@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'tipo_negocio',
        'propietario_display',
        'activo',
        'direccion',
        'metodos_pago_display',
        'loyverse_configurado',
        'fecha_creacion',
    )
    list_filter = ('activo', 'tipo_negocio', 'modo_asignacion_default')
    search_fields = ('nombre', 'propietario_perfil__user__username', 'direccion')
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [RadioEnvioInline, CuadranteEnvioInline]

    fieldsets = (
        ('Información general', {
            'fields': ('propietario_perfil', 'nombre', 'slug', 'descripcion', 'tipo_negocio', 'activo')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'url', 'horario_atencion')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'latitud', 'longitud')
        }),
        ('Imágenes', {
            'fields': ('logo',)
        }),
        ('Métodos de pago', {
            'fields': (
                'acepta_efectivo',
                'acepta_transferencia',
                'banco', 'tipo_cuenta', 'numero_cuenta',
                'titular_cuenta', 'rut_titular', 'email_transferencia',
                'acepta_link_pago',
                'link_pago_url', 'instrucciones_link_pago',
            )
        }),
        ('Repartidores', {
            'fields': ('modo_asignacion_default',)
        }),
        ('Integración Loyverse', {
            'fields': ('loyverse_activo', 'loyverse_token', 'loyverse_store_id'),
            'classes': ('collapse',),
            'description': '⚠️ El token es sensible. No lo compartas ni lo publiques.'
        }),
    )

    def propietario_display(self, obj):
        if obj.propietario_perfil:
            return obj.propietario_perfil.user.username
        return "N/A"
    propietario_display.short_description = 'Propietario'

    def metodos_pago_display(self, obj):
        return ", ".join(obj.metodos_pago_activos) or "Ninguno"
    metodos_pago_display.short_description = 'Métodos de pago'

    def loyverse_configurado(self, obj):
        return obj.loyverse_configurado
    loyverse_configurado.boolean = True
    loyverse_configurado.short_description = 'Loyverse'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if hasattr(request.user, 'seller_profile'):
                obj.propietario_perfil = request.user.seller_profile
        super().save_model(request, obj, form, change)


# ------------------------------------------------------------------
# RADIO DE ENVÍO
# ------------------------------------------------------------------
@admin.register(RadioEnvio)
class RadioEnvioAdmin(admin.ModelAdmin):
    list_display = ('id', 'tienda', 'distancia_max_km', 'costo_envio', 'envio_gratis')
    list_filter = ('tienda', 'envio_gratis')
    search_fields = ('tienda__nombre',)


# ------------------------------------------------------------------
# CUADRANTE DE ENVÍO
# ------------------------------------------------------------------
@admin.register(CuadranteEnvio)
class CuadranteEnvioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tienda',
        'nombre',
        'descripcion',
        'costo_envio',
        'envio_gratis',
        'activo',
        'fecha_creacion',
    )
    list_filter = ('tienda', 'envio_gratis', 'activo')
    search_fields = ('tienda__nombre', 'nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)

    fieldsets = (
        ('Información del sector', {
            'fields': ('tienda', 'nombre', 'descripcion', 'activo')
        }),
        ('Costo de envío', {
            'fields': ('costo_envio', 'envio_gratis')
        }),
        ('Polígono', {
            'fields': ('poligono',),
            'description': (
                'Lista de coordenadas en formato JSON: '
                '[{"lat": -37.79, "lng": -72.70}, ...]. '
                'Se genera automáticamente desde el mapa en el frontend.'
            )
        }),
        ('Control', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',),
        }),
    )