# usuarios/permissions.py
# modificacion 10/8/2025

from rest_framework import permissions
# Importa los modelos necesarios directamente
from .models import UserType, SellerProfile

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir que solo los propietarios de un objeto lo editen.
    Las solicitudes de lectura (GET, HEAD, OPTIONS) están permitidas para todos.
    Las solicitudes de escritura (POST, PUT, PATCH, DELETE) solo están permitidas para el propietario.
    """

    def has_object_permission(self, request, view, obj):
        # Los permisos de lectura están permitidos para cualquier solicitud.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Los permisos de escritura solo están permitidos para el propietario del objeto.
        # Asumimos que el objeto tiene un atributo 'user' o 'cliente.user'
        # que apunta al usuario que lo posee.

        # Para modelos que tienen un campo 'user' directo (ej. BuyerProfile, SellerProfile)
        if hasattr(obj, 'user') and obj.user:
            return obj.user == request.user

        # Para modelos que están relacionados con un Cliente, y el Cliente tiene un 'user' (ej. Direccion)
        if hasattr(obj, 'cliente') and hasattr(obj.cliente, 'user') and obj.cliente.user:
            return obj.cliente.user == request.user

        # Para modelos que están relacionados con una Tienda, y la Tienda tiene un 'propietario_perfil'
        # que a su vez tiene un 'user' (ej. Categoria, SubCategoria, Producto)
        if hasattr(obj, 'tienda') and hasattr(obj.tienda, 'propietario_perfil') and hasattr(obj.tienda.propietario_perfil, 'user') and obj.tienda.propietario_perfil.user:
            return obj.tienda.propietario_perfil.user == request.user

        # Si el objeto no tiene una relación de propiedad clara o el usuario no está autenticado, denegar.
        return False


class IsSeller(permissions.BasePermission):
    """
    Permite el acceso solo a usuarios autenticados que tienen el user_type 'SELLER'.
    También verifica si el perfil de vendedor está completo.
    """
    def has_permission(self, request, view):
        # Un usuario debe estar autenticado para ser considerado un vendedor.
        if not request.user or not request.user.is_authenticated:
            return False

        # Verifica si el usuario es de tipo SELLER
        if request.user.user_type != UserType.SELLER:
            return False

        # Opcional: Verifica si el perfil de vendedor está completo
        if hasattr(request.user, 'seller_profile'):
            return request.user.seller_profile.is_complete()

        return False

    def has_object_permission(self, request, view, obj):
        # Permite la lectura del objeto a cualquier vendedor.
        if request.method in permissions.SAFE_METHODS:
            return self.has_permission(request, view)

        # Para operaciones de escritura, el usuario debe ser el propietario.
        # Delega la verificación de la propiedad a otra clase o al ViewSet.
        # Este permiso se enfoca solo en el tipo de usuario.
        return self.has_permission(request, view)


