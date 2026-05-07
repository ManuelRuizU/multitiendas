# usuarios/permissions.py
from rest_framework import permissions


# ------------------------------------------------------------------
# 1. PERMISO DE PROPIEDAD
# Permite lectura a todos, escritura solo al dueño del objeto.
# Cubre 3 casos en cascada según la estructura del modelo.
# ------------------------------------------------------------------
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a todos.
    Escritura solo al propietario del objeto.
    Cubre: User directo, via Tienda, via Cliente.
    """
    def has_object_permission(self, request, view, obj):
        # Lectura siempre permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # 1. Propiedad directa (SellerProfile, BuyerProfile)
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # 2. Via Tienda (Producto, Categoria, RadioEnvio, CuadranteEnvio)
        if hasattr(obj, 'tienda'):
            return obj.tienda.propietario_perfil.user == request.user

        # 3. Via Cliente (Direccion)
        if hasattr(obj, 'cliente'):
            return obj.cliente.user == request.user

        return False


# ------------------------------------------------------------------
# 2. PERMISO DE VENDEDOR
# El usuario debe tener is_vendedor=True Y tener un SellerProfile.
# Combinamos ambas verificaciones para máxima seguridad.
# ------------------------------------------------------------------
class IsSeller(permissions.BasePermission):
    """
    Garantiza que el usuario sea un vendedor activo con perfil completo.
    Usa is_vendedor=True + existencia de seller_profile.
    """
    message = "Debes completar tu registro como vendedor para acceder a esta sección."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_vendedor and
            hasattr(request.user, 'seller_profile')
        )

    def has_object_permission(self, request, view, obj):
        # El objeto es una Tienda
        if hasattr(obj, 'propietario_perfil'):
            return obj.propietario_perfil.user == request.user

        # El objeto pertenece a una Tienda (Producto, RadioEnvio, etc.)
        if hasattr(obj, 'tienda'):
            return obj.tienda.propietario_perfil.user == request.user

        return True


# ------------------------------------------------------------------
# 3. PERMISO DE REPARTIDOR
# El usuario debe tener is_repartidor=True Y tener un Repartidor profile.
# ------------------------------------------------------------------
class IsRepartidor(permissions.BasePermission):
    """
    Garantiza que el usuario sea un repartidor activo con perfil completo.
    Usa is_repartidor=True + existencia de repartidor_profile.
    """
    message = "Debes completar tu registro como repartidor para acceder a esta sección."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_repartidor and
            hasattr(request.user, 'repartidor_profile')
        )

    def has_object_permission(self, request, view, obj):
        # Solo puede ver/modificar pedidos asignados a él
        if hasattr(obj, 'repartidor'):
            return obj.repartidor == request.user.repartidor_profile
        return True


# ------------------------------------------------------------------
# 4. PERMISO DE CLIENTE
# El usuario debe estar autenticado y tener is_cliente=True.
# ------------------------------------------------------------------
class IsCliente(permissions.BasePermission):
    """
    Garantiza que el usuario sea un cliente registrado.
    """
    message = "Debes iniciar sesión como cliente para acceder a esta sección."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_cliente
        )

    def has_object_permission(self, request, view, obj):
        # Solo puede ver/modificar sus propios datos
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'cliente'):
            return obj.cliente.user == request.user
        return True


# ------------------------------------------------------------------
# 5. PERMISO DE VENDEDOR O ADMIN
# Útil para vistas que pueden acceder tanto vendedores como staff.
# ------------------------------------------------------------------
class IsSellerOrAdmin(permissions.BasePermission):
    """
    Permite acceso a vendedores activos o administradores del sistema.
    """
    message = "Debes ser vendedor o administrador para acceder."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return (
            request.user.is_vendedor and
            hasattr(request.user, 'seller_profile')
        )