# tiendas/models.py
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from usuarios.models import SellerProfile
from decimal import Decimal
import math


# ------------------------------------------------------------------
# UTILIDAD: Algoritmo Ray Casting
# Detecta si un punto (lat, lng) está dentro de un polígono.
# El polígono es una lista de {"lat": x, "lng": y}.
# ------------------------------------------------------------------
def punto_en_poligono(lat, lng, poligono):
    """
    Implementación del algoritmo Ray Casting para detectar si un punto
    está dentro de un polígono definido por una lista de coordenadas.

    Args:
        lat (float): Latitud del punto a verificar.
        lng (float): Longitud del punto a verificar.
        poligono (list): Lista de dicts con claves 'lat' y 'lng'.
                         Ej: [{"lat": -37.79, "lng": -72.70}, ...]

    Returns:
        bool: True si el punto está dentro del polígono, False si no.
    """
    n = len(poligono)
    dentro = False
    j = n - 1
    for i in range(n):
        xi, yi = poligono[i]['lng'], poligono[i]['lat']
        xj, yj = poligono[j]['lng'], poligono[j]['lat']
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            dentro = not dentro
        j = i
    return dentro


# ------------------------------------------------------------------
# 1. TIENDA
# ------------------------------------------------------------------
class Tienda(models.Model):

    propietario_perfil = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name="tiendas_gestionadas",
        verbose_name="Perfil del Vendedor Propietario",
        help_text="El perfil del vendedor asociado a esta tienda."
    )

    # --- Tipo de negocio ---
    # Define el comportamiento por defecto de los productos.
    # COMIDA → productos bajo demanda (stock_ilimitado=True por defecto)
    # RETAIL → productos con stock real (stock_ilimitado=False por defecto)
    TIPO_NEGOCIO_CHOICES = [
        ('COMIDA',    'Comida y Bebidas'),
        ('RETAIL',    'Tienda / Retail'),
        ('SERVICIOS', 'Servicios'),
        ('OTRO',      'Otro'),
    ]
    tipo_negocio = models.CharField(
        "Tipo de negocio",
        max_length=20,
        choices=TIPO_NEGOCIO_CHOICES,
        default='COMIDA',
        help_text=(
            "Define el tipo de negocio. "
            "COMIDA: productos bajo demanda, sin control de stock por defecto. "
            "RETAIL: productos con stock real, se desactivan al llegar a 0."
        )
    )

    nombre = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True, blank=True, max_length=150)
    descripcion = models.TextField(blank=True)

    # --- Ubicación ---
    direccion = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Contacto ---
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    horario_atencion = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to="logos_tiendas/", blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    # ------------------------------------------------------------------
    # MÉTODOS DE PAGO
    # ------------------------------------------------------------------
    acepta_efectivo = models.BooleanField(
        "Acepta efectivo",
        default=True,
        help_text="El cliente paga en efectivo al momento de la entrega o retiro."
    )
    acepta_transferencia = models.BooleanField(
        "Acepta transferencia bancaria",
        default=False,
        help_text="El cliente realiza una transferencia bancaria."
    )
    acepta_link_pago = models.BooleanField(
        "Acepta link de pago",
        default=False,
        help_text="El emprendedor comparte un link de pago (Flow, Khipu, MercadoPago, etc.)."
    )

    # --- Datos bancarios para transferencia ---
    BANCO_CHOICES = [
        ('Banco de Chile', 'Banco de Chile'),
        ('Banco Estado', 'Banco Estado'),
        ('Banco BCI', 'Banco BCI'),
        ('Banco Santander', 'Banco Santander'),
        ('Banco Scotiabank', 'Banco Scotiabank'),
        ('Banco Itaú', 'Banco Itaú'),
        ('Banco Falabella', 'Banco Falabella'),
        ('Banco Ripley', 'Banco Ripley'),
        ('Banco Security', 'Banco Security'),
        ('Banco BICE', 'Banco BICE'),
        ('Coopeuch', 'Coopeuch'),
        ('Otro', 'Otro'),
    ]

    TIPO_CUENTA_CHOICES = [
        ('Cuenta Corriente', 'Cuenta Corriente'),
        ('Cuenta Vista', 'Cuenta Vista'),
        ('Cuenta RUT', 'Cuenta RUT'),
        ('Cuenta de Ahorro', 'Cuenta de Ahorro'),
    ]

    banco = models.CharField(
        "Banco", max_length=50, choices=BANCO_CHOICES, blank=True, null=True
    )
    tipo_cuenta = models.CharField(
        "Tipo de cuenta", max_length=30, choices=TIPO_CUENTA_CHOICES, blank=True, null=True
    )
    numero_cuenta = models.CharField(
        "Número de cuenta", max_length=30, blank=True, null=True
    )
    titular_cuenta = models.CharField(
        "Titular de la cuenta", max_length=150, blank=True, null=True
    )
    rut_titular = models.CharField(
        "RUT del titular", max_length=12, blank=True, null=True
    )
    email_transferencia = models.EmailField(
        "Email para transferencia", blank=True, null=True
    )

    # --- Link de pago ---
    link_pago_url = models.URLField(
        "Link de pago", blank=True, null=True,
        help_text="Link de pago (Flow, Khipu, MercadoPago, etc.)."
    )
    instrucciones_link_pago = models.CharField(
        "Instrucciones del link de pago", max_length=255, blank=True, null=True,
        help_text="Ej: 'Paga por Flow e indica tu número de pedido'."
    )

    # ------------------------------------------------------------------
    # CONFIGURACIÓN DE REPARTIDORES
    # ------------------------------------------------------------------
    MODO_ASIGNACION_CHOICES = [
        ('LIBRE',   'Libre — cualquier repartidor puede tomarlo'),
        ('CERRADO', 'Cerrado — el emprendedor lo asigna manualmente'),
    ]
    modo_asignacion_default = models.CharField(
        "Modo de asignación por defecto",
        max_length=10,
        choices=MODO_ASIGNACION_CHOICES,
        default='LIBRE',
        help_text=(
            "Define cómo se asignan los pedidos a los repartidores por defecto. "
            "LIBRE: cualquier repartidor activo puede tomarlo. "
            "CERRADO: el emprendedor lo asigna manualmente."
        )
    )

    # ------------------------------------------------------------------
    # INTEGRACIÓN CON LOYVERSE
    # Cada emprendedor conecta su propia cuenta de Loyverse.
    # El token se obtiene desde el Back Office de Loyverse → Configuración → API.
    #
    # IMPORTANTE (V2): loyverse_token debe encriptarse antes de producción
    # usando django-encrypted-model-fields o similar.
    # Ejemplo: pip install django-encrypted-model-fields
    # ------------------------------------------------------------------
    loyverse_token = models.CharField(
        "Token API de Loyverse",
        max_length=255,
        blank=True,
        null=True,
        help_text=(
            "Token de acceso a la API de Loyverse. "
            "Se obtiene en: Loyverse Back Office → Configuración → API. "
            "⚠️ Mantén este token seguro, no lo compartas."
        )
    )
    loyverse_store_id = models.CharField(
        "ID de tienda en Loyverse",
        max_length=100,
        blank=True,
        null=True,
        help_text=(
            "ID de la tienda en Loyverse. Necesario para crear receipts "
            "asociados a la tienda correcta."
        )
    )
    loyverse_activo = models.BooleanField(
        "Integración con Loyverse activa",
        default=False,
        help_text=(
            "Activa la sincronización automática con Loyverse al confirmar pedidos. "
            "Requiere token y store ID configurados."
        )
    )

    # ------------------------------------------------------------------
    # HOOKS
    # ------------------------------------------------------------------
    def clean(self):
        # Perfil del vendedor completo
        if self.propietario_perfil and not self.propietario_perfil.is_complete():
            raise ValidationError(
                "Debes completar todos los datos obligatorios de tu perfil de vendedor "
                "antes de crear una tienda."
            )

        # Al menos un método de pago activo
        if not any([self.acepta_efectivo, self.acepta_transferencia, self.acepta_link_pago]):
            raise ValidationError(
                "Debes activar al menos un método de pago para tu tienda."
            )

        # Datos bancarios obligatorios si acepta transferencia
        if self.acepta_transferencia:
            campos_transferencia = {
                'banco': self.banco,
                'tipo_cuenta': self.tipo_cuenta,
                'numero_cuenta': self.numero_cuenta,
                'titular_cuenta': self.titular_cuenta,
                'rut_titular': self.rut_titular,
                'email_transferencia': self.email_transferencia,
            }
            faltantes = [k for k, v in campos_transferencia.items() if not v]
            if faltantes:
                raise ValidationError(
                    f"Si aceptas transferencia, completa todos los datos bancarios. "
                    f"Faltan: {', '.join(faltantes)}."
                )

        # URL obligatoria si acepta link de pago
        if self.acepta_link_pago and not self.link_pago_url:
            raise ValidationError(
                "Si aceptas link de pago, debes ingresar la URL del link."
            )

        # Si activa Loyverse, token y store ID son obligatorios
        if self.loyverse_activo:
            if not self.loyverse_token:
                raise ValidationError(
                    "Para activar la integración con Loyverse debes ingresar el token API."
                )
            if not self.loyverse_store_id:
                raise ValidationError(
                    "Para activar la integración con Loyverse debes ingresar el ID de tu tienda en Loyverse."
                )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            while Tienda.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    # ------------------------------------------------------------------
    # LÓGICA DE COSTO DE ENVÍO
    # Prioridad: Cuadrante > Radio > No despacha
    # ------------------------------------------------------------------

    def calcular_distancia_km(self, lat_cliente, lng_cliente):
        """
        Calcula la distancia en km entre la tienda y el cliente
        usando la fórmula de Haversine.
        """
        if not self.latitud or not self.longitud:
            return None

        R = 6371  # Radio de la Tierra en km
        lat1 = math.radians(float(self.latitud))
        lat2 = math.radians(float(lat_cliente))
        dlat = math.radians(float(lat_cliente) - float(self.latitud))
        dlng = math.radians(float(lng_cliente) - float(self.longitud))

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def verificar_cuadrante(self, lat_cliente, lng_cliente):
        """
        Verifica si la dirección del cliente cae dentro de algún cuadrante activo.
        Retorna el cuadrante si hay coincidencia, None si no.
        """
        for cuadrante in self.cuadrantes.filter(activo=True):
            if cuadrante.contiene_punto(lat_cliente, lng_cliente):
                return cuadrante
        return None

    def calcular_costo_envio(self, lat_cliente, lng_cliente):
        """
        Calcula el costo de envío para una dirección dada.

        Lógica de prioridad:
        1. ¿La dirección cae en un cuadrante activo? → precio del cuadrante (anula el radio)
        2. ¿No hay cuadrante? → precio según radio de distancia
        3. ¿Fuera del radio máximo configurado? → None (no se despacha a esa dirección)

        Returns:
            Decimal: costo de envío en pesos chilenos.
            None: si la dirección está fuera del área de despacho.
        """
        # 1. Cuadrante tiene prioridad
        cuadrante = self.verificar_cuadrante(lat_cliente, lng_cliente)
        if cuadrante:
            return Decimal('0') if cuadrante.envio_gratis else cuadrante.costo_envio

        # 2. Aplicar radio por distancia
        distancia_km = self.calcular_distancia_km(lat_cliente, lng_cliente)
        if distancia_km is None:
            return None

        radio = self.radios_envio.filter(
            distancia_max_km__gte=Decimal(str(distancia_km))
        ).order_by('distancia_max_km').first()

        if radio:
            return Decimal('0') if radio.envio_gratis else radio.costo_envio

        # 3. Fuera de cobertura
        return None

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------

    @property
    def metodos_pago_activos(self):
        """Lista legible de métodos de pago activos."""
        metodos = []
        if self.acepta_efectivo:
            metodos.append('Efectivo')
        if self.acepta_transferencia:
            metodos.append('Transferencia bancaria')
        if self.acepta_link_pago:
            metodos.append('Link de pago')
        return metodos

    @property
    def stock_ilimitado_default(self):
        """
        Retorna el valor por defecto de stock_ilimitado según el tipo de negocio.
        Se usa al crear nuevos productos para pre-configurar el campo correctamente.
        
        COMIDA / SERVICIOS → True  (bajo demanda, no controla stock)
        RETAIL / OTRO      → False (stock real, se desactiva al llegar a 0)
        """
        return self.tipo_negocio in ['COMIDA', 'SERVICIOS']

    @property
    def loyverse_configurado(self):
        """
        Verifica si la integración con Loyverse está lista para usarse.
        Útil para mostrar el estado en el panel del emprendedor.
        """
        return bool(self.loyverse_activo and self.loyverse_token and self.loyverse_store_id)

    @property
    def datos_transferencia_whatsapp(self):
        """Texto formateado con datos de transferencia para el mensaje de WhatsApp."""
        if not self.acepta_transferencia:
            return None
        return (
            f"🏦 *Datos para transferencia:*\n"
            f"Banco: {self.banco}\n"
            f"Tipo de cuenta: {self.tipo_cuenta}\n"
            f"Número de cuenta: {self.numero_cuenta}\n"
            f"Titular: {self.titular_cuenta}\n"
            f"RUT: {self.rut_titular}\n"
            f"Email: {self.email_transferencia}"
        )

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Tiendas"


# ------------------------------------------------------------------
# 2. RADIO DE ENVÍO
# El emprendedor solo ingresa el límite máximo de cada radio.
# El sistema busca el radio más pequeño >= distancia del cliente.
#
# Ejemplo:
#   Radio 1 → hasta 1 km  → GRATIS
#   Radio 2 → hasta 3 km  → $1.000
#   Radio 3 → hasta 5 km  → $2.000
#   Cliente a 2.3 km → entra en "hasta 3 km" → $1.000
#   Cliente a 6.0 km → fuera de cobertura → no despacha
# ------------------------------------------------------------------
class RadioEnvio(models.Model):
    tienda = models.ForeignKey(
        Tienda, on_delete=models.CASCADE, related_name="radios_envio"
    )
    distancia_max_km = models.DecimalField(
        "Distancia máxima (km)",
        max_digits=4,
        decimal_places=1,
        help_text="Límite superior de este radio. Ej: 1, 3, 5. Cubre desde 0 hasta este valor."
    )
    costo_envio = models.DecimalField(
        "Costo de envío ($)",
        max_digits=10,
        decimal_places=0,
        default=0,
        help_text="Costo en pesos chilenos. Se ignora si 'envío gratis' está activo."
    )
    envio_gratis = models.BooleanField(
        "Envío gratis",
        default=False,
        help_text="Si está activo, el envío es gratuito para este radio."
    )

    class Meta:
        ordering = ["distancia_max_km"]
        unique_together = ("tienda", "distancia_max_km")
        verbose_name = "Radio de Envío"
        verbose_name_plural = "Radios de Envío"

    def __str__(self):
        if self.envio_gratis:
            return f"{self.tienda.nombre} → hasta {self.distancia_max_km} km (GRATIS)"
        return f"{self.tienda.nombre} → hasta {self.distancia_max_km} km = ${self.costo_envio}"


# ------------------------------------------------------------------
# 3. CUADRANTE DE ENVÍO
# Zona específica definida por un polígono dibujado en el mapa.
# Tiene PRIORIDAD sobre el radio — si el cliente cae en un cuadrante,
# se cobra el precio del cuadrante y se ignora el radio.
#
# Ejemplos de uso:
#   "Las Acequias" → $2.500 (cerro sin pavimento, difícil acceso)
#   "Sector Industrial" → GRATIS (zona prioritaria del emprendedor)
#   "Villa El Bosque" → $1.500 (zona normal pero fuera del radio estándar)
# ------------------------------------------------------------------
class CuadranteEnvio(models.Model):
    tienda = models.ForeignKey(
        Tienda, on_delete=models.CASCADE, related_name="cuadrantes"
    )
    nombre = models.CharField(
        "Nombre del sector",
        max_length=100,
        help_text="Nombre descriptivo. Ej: 'Las Acequias', 'Sector Norte', 'Villa El Bosque'."
    )
    descripcion = models.CharField(
        "Descripción interna",
        max_length=255,
        blank=True,
        null=True,
        help_text="Nota interna. Ej: 'Cerro sin pavimento, difícil acceso en invierno'."
    )
    poligono = models.JSONField(
        "Coordenadas del polígono",
        help_text=(
            "Lista de coordenadas que definen el área del sector. "
            "Formato: [{'lat': -37.79, 'lng': -72.70}, ...]. "
            "Se genera automáticamente al dibujar en el mapa."
        )
    )
    costo_envio = models.DecimalField(
        "Costo de envío ($)",
        max_digits=10,
        decimal_places=0,
        default=0,
        help_text="Costo en pesos chilenos. Se ignora si 'envío gratis' está activo."
    )
    envio_gratis = models.BooleanField(
        "Envío gratis",
        default=False,
        help_text="Si está activo, el envío es gratuito para este sector."
    )
    activo = models.BooleanField(
        "Activo",
        default=True,
        help_text="Desactiva el cuadrante sin eliminarlo. Útil para temporadas o condiciones especiales."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Cuadrante de Envío"
        verbose_name_plural = "Cuadrantes de Envío"

    def __str__(self):
        estado = "ACTIVO" if self.activo else "INACTIVO"
        if self.envio_gratis:
            return f"{self.tienda.nombre} → {self.nombre} (GRATIS) [{estado}]"
        return f"{self.tienda.nombre} → {self.nombre} = ${self.costo_envio} [{estado}]"

    def contiene_punto(self, lat, lng):
        """
        Verifica si un punto (lat, lng) está dentro de este cuadrante.
        Usa el algoritmo Ray Casting definido al inicio del archivo.
        """
        return punto_en_poligono(lat, lng, self.poligono)