# usuarios/permissions.py

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso para que solo el dueño del dato pueda editarlo.
    Ideal para Direcciones, Perfiles y Objetos ligados a la tienda.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # 1. Propiedad directa (User, SellerProfile)
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # 2. Relación a través de Tienda (Productos, Categorías, Cuadrantes)
        if hasattr(obj, 'tienda'):
            return obj.tienda.propietario_perfil.user == request.user

        # 3. Relación a través de Cliente (Direcciones)
        if hasattr(obj, 'cliente'):
            return obj.cliente.user == request.user

        return False

class IsSeller(permissions.BasePermission):
    """
    Garantiza que el usuario sea un vendedor activo.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'seller_profile')
        )

    def has_object_permission(self, request, view, obj):
        # Si el objeto es una Tienda, el usuario debe ser su dueño
        if hasattr(obj, 'propietario_perfil'):
            return obj.propietario_perfil.user == request.user
        
        # Si el objeto pertenece a una tienda (Producto/Radio)
        if hasattr(obj, 'tienda'):
            return obj.tienda.propietario_perfil.user == request.user
            
        return True