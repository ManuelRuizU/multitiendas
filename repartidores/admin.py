# repartidores/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Repartidor


@admin.register(Repartidor)
class RepartidorAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_display',
        'telefono',
        'get_vehiculo_display',
        'estado',
        'cantidad_pedidos_activos',
        'tiendas_display',
        'fecha_registro',
    )
    list_filter = ('estado', 'vehiculo')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'telefono',
    )
    filter_horizontal = ('tiendas',)  # Widget más cómodo para ManyToMany
    readonly_fields = ('fecha_registro',)

    fieldsets = (
        ('Datos personales', {
            'fields': ('user', 'telefono', 'foto', 'vehiculo')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Tiendas asignadas', {
            'fields': ('tiendas',)
        }),
        ('Notas internas', {
            'fields': ('notas',),
            'classes': ('collapse',),
        }),
        ('Control', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',),
        }),
    )

    def nombre_display(self, obj):
        nombre = obj.user.get_full_name() or obj.user.username
        url = reverse('admin:usuarios_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, nombre)
    nombre_display.short_description = 'Repartidor'

    def tiendas_display(self, obj):
        tiendas = obj.tiendas.all()
        if not tiendas:
            return "Sin tiendas asignadas"
        return ", ".join(t.nombre for t in tiendas)
    tiendas_display.short_description = 'Tiendas'

    def cantidad_pedidos_activos(self, obj):
        count = obj.cantidad_pedidos_activos
        color = 'green' if count == 0 else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    cantidad_pedidos_activos.short_description = 'Pedidos activos'