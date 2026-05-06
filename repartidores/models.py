# repartidores/models.py
from django.db import models
from django.conf import settings
from tiendas.models import Tienda


# ------------------------------------------------------------------
# 1. REPARTIDOR
# ------------------------------------------------------------------
class Repartidor(models.Model):

    # --- Estados del repartidor ---
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),   # Activo, sin pedidos, listo para tomar
        ('EN_RUTA',    'En ruta'),      # Activo, con pedidos asignados, en camino
        ('INACTIVO',   'Inactivo'),     # No está trabajando
    ]

    # --- Tipo de vehículo ---
    VEHICULO_CHOICES = [
        ('BICICLETA', 'Bicicleta'),
        ('MOTO',      'Moto'),
        ('AUTO',      'Auto'),
        ('FURGON',    'Furgón'),
        ('A_PIE',     'A pie'),
        ('OTRO',      'Otro'),
    ]

    # El repartidor tiene su propio login en la app
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='repartidor_profile',
        verbose_name="Usuario",
        help_text="Cuenta de usuario del repartidor para acceder a la app."
    )

    # Hoy trabaja para una tienda, en el futuro para muchas (ManyToMany)
    # Para agregar una tienda: repartidor.tiendas.add(tienda)
    # Para ver sus tiendas: repartidor.tiendas.all()
    tiendas = models.ManyToManyField(
        Tienda,
        related_name='repartidores',
        blank=True,
        verbose_name="Tiendas",
        help_text="Tiendas para las que trabaja este repartidor."
    )

    # --- Datos personales ---
    telefono = models.CharField(
        "Teléfono",
        max_length=20,
        blank=False,
        null=False,
        help_text="Teléfono de contacto del repartidor."
    )
    vehiculo = models.CharField(
        "Vehículo",
        max_length=20,
        choices=VEHICULO_CHOICES,
        default='MOTO',
        help_text="Tipo de vehículo que usa para los repartos."
    )
    foto = models.ImageField(
        "Foto",
        upload_to='repartidores/',
        blank=True,
        null=True,
        help_text="Foto del repartidor. Útil para que el cliente lo identifique."
    )

    # --- Estado actual ---
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=ESTADO_CHOICES,
        default='INACTIVO',
        help_text=(
            "Estado actual del repartidor. "
            "El emprendedor ve este estado para decidir a quién asignar un pedido."
        )
    )

    # --- Control ---
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(
        "Notas internas",
        blank=True,
        null=True,
        help_text="Notas internas del emprendedor sobre este repartidor."
    )

    class Meta:
        verbose_name = "Repartidor"
        verbose_name_plural = "Repartidores"
        ordering = ['estado', 'user__first_name']

    def __str__(self):
        nombre = self.user.get_full_name() or self.user.username
        return f"{nombre} — {self.get_estado_display()} ({self.get_vehiculo_display()})"

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------
    @property
    def esta_activo(self):
        """True si el repartidor está disponible o en ruta (trabajando hoy)."""
        return self.estado in ['DISPONIBLE', 'EN_RUTA']

    @property
    def pedidos_activos(self):
        """
        Retorna los pedidos asignados al repartidor que aún no han sido entregados,
        ordenados por hora de entrega estimada.
        Este es el orden de reparto que ve el repartidor en su app.
        """
        return self.pedidos_asignados.filter(
            status__in=['CONFIRMED', 'PREPARING', 'ON_THE_WAY']
        ).order_by('hora_entrega_est')

    @property
    def cantidad_pedidos_activos(self):
        """Cantidad de pedidos activos. Útil para el panel del emprendedor."""
        return self.pedidos_activos.count()

    def actualizar_estado(self):
        """
        Actualiza automáticamente el estado del repartidor según sus pedidos activos.
        Llamar después de asignar o completar un pedido.
        """
        if self.estado == 'INACTIVO':
            return  # Si está inactivo, no cambia automáticamente
        if self.cantidad_pedidos_activos > 0:
            self.estado = 'EN_RUTA'
        else:
            self.estado = 'DISPONIBLE'
        self.save(update_fields=['estado'])

