# repartidores/models.py
from django.db import models
from django.conf import settings
from tiendas.models import Tienda


# ------------------------------------------------------------------
# REPARTIDOR
# Se crea cuando un usuario completa el registro como repartidor.
# Al guardarse activa is_repartidor=True en el CustomUser,
# igual que SellerProfile activa is_vendedor=True.
# ------------------------------------------------------------------
class Repartidor(models.Model):

    # --- Estados del repartidor ---
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),   # Activo, sin pedidos, listo para tomar
        ('EN_RUTA',    'En ruta'),      # Activo, con pedidos asignados, en camino
        ('INACTIVO',   'Inactivo'),     # No está trabajando hoy
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

    # --- Usuario asociado ---
    # El repartidor tiene su propio login en la app.
    # Al guardarse, activa is_repartidor=True en el CustomUser.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='repartidor_profile',
        verbose_name="Usuario",
        help_text="Cuenta de usuario del repartidor para acceder a la app."
    )

    # --- Tiendas asignadas ---
    # Hoy trabaja para una tienda, en el futuro para muchas.
    # ManyToMany permite escalar sin cambiar el modelo.
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Activar rol de repartidor en el usuario
        # Mismo patrón que SellerProfile con is_vendedor
        if not self.user.is_repartidor:
            self.user.is_repartidor = True
            self.user.save(update_fields=['is_repartidor'])

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------
    @property
    def esta_activo(self):
        """True si el repartidor está trabajando hoy (disponible o en ruta)."""
        return self.estado in ['DISPONIBLE', 'EN_RUTA']

    @property
    def pedidos_activos(self):
        """
        Pedidos asignados al repartidor que aún no han sido entregados,
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
        Actualiza automáticamente el estado según los pedidos activos.
        Llamar después de asignar o completar un pedido.
        Si está INACTIVO no cambia automáticamente — solo el emprendedor
        puede marcarlo como DISPONIBLE.
        """
        if self.estado == 'INACTIVO':
            return
        nuevo_estado = 'EN_RUTA' if self.cantidad_pedidos_activos > 0 else 'DISPONIBLE'
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            self.save(update_fields=['estado'])