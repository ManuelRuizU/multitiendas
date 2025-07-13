# tiendas/admin.py
from django.contrib import admin
from .models import Tienda, RadioEnvio

# Inline para Radios de Envío dentro del admin de Tienda
class RadioEnvioInline(admin.TabularInline):
    model = RadioEnvio
    extra = 1 # Muestra 1 campo extra vacío para añadir fácilmente

@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'vendedor', 'activo', 'direccion', 'telefono', 'fecha_creacion')
    list_filter = ('activo', 'vendedor')
    search_fields = ('nombre', 'vendedor__user__username', 'direccion')
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [RadioEnvioInline]

admin.site.register(RadioEnvio)