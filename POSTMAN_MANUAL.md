Apéndice: Guía Completa de Postman para tu Plataforma Multitienda

Esta guía te proporcionará los pasos detallados para realizar las operaciones más comunes en tu API de Django utilizando Postman. Asegúrate de que tu servidor de desarrollo Django (python manage.py runserver) esté activo y corriendo antes de comenzar.

Conceptos Clave en Postman:

    Método: Tipo de solicitud HTTP (GET, POST, PUT, PATCH, DELETE).

    URL: La dirección del endpoint de tu API.

    Headers: Información adicional enviada con la solicitud (ej., Content-Type, Authorization).

    Body: Los datos que envías con la solicitud (especialmente para POST/PUT/PATCH).

    Authorization: Para solicitudes que requieren que el usuario esté logueado, usarás Token <tu_token_aqui>.

Paso 0: Configuración Inicial en Postman

    Crea una Nueva Colección: En la barra lateral izquierda de Postman, haz clic en "Collections" y luego en el + para crear una "New Collection". Nómbrala algo como "Mi Plataforma Multitienda API". Esto te ayudará a organizar tus solicitudes.

    Crea un Nuevo Entorno (Opcional pero Recomendado):

        Haz clic en el ícono de "Environments" (parece un ojo) en la parte superior derecha de Postman, luego en "Add".

        Nómbralo "Desarrollo Local".

        Añade una variable: base_url con el valor http://127.0.0.1:8000.

        Añade otra variable: auth_token (déjala vacía por ahora, la llenaremos cuando obtengamos un token).

        Selecciona este entorno "Desarrollo Local" en el desplegable de entornos (arriba a la derecha).

        Ahora, en lugar de http://127.0.0.1:8000, podrás usar {{base_url}} en tus URLs.

Paso 1: Autenticación - Creación y Login de Usuarios

Para interactuar con gran parte de tu API, necesitarás un token de autenticación.

1.1. Crear un Usuario (Comprador)

    Método: POST

    http://127.0.0.1:8000/api/usuarios/register/

    Headers:

        Content-Type: application/json

    Body (raw - JSON):
    JSON

         
   
    Enviar y Verificar: Deberías recibir un 201 Created con los datos del usuario y un token. Guarda este token. Puedes copiarlo y pegarlo en la variable auth_token de tu entorno de Postman para el comprador.

1.2. Crear un Usuario (Vendedor)

    Método: POST

    http://127.0.0.1:8000/api/usuarios/register-seller/

    Headers:

        Content-Type: application/json

    Body (raw - JSON) EJEMPLO:
    JSON

    {
    "username": "vendedor_test_005",
    "email": "vendedor.test.005@example.com",
    "password": "otra_password_segura123",
    "password2": "otra_password_segura123",
    "first_name": "Ana",
    "last_name": "Pérez",
    "telefono_vendedor": "+56911112222",
    "rut": "55667788-9",
    "razon_social": "Comercial Ana S.A.",
    "giro": "Venta de productos electrónicos",
    "direccion_fiscal": "Avenida Siempre Viva 742, Valparaíso"
    }

    RESPUESTA: 201 Created
               { "message": "Vendedor registrado exitosamente con perfil completo.",
                 "user_id": 11
                }



    Enviar y Verificar: Deberías recibir un 201 Created con los datos del vendedor y su token. Guarda este token en otra variable de entorno (ej. seller_auth_token) o simplemente tenlo a mano.

1.3. Iniciar Sesión (para obtener un token si no lo tienes)

Si por alguna razón pierdes un token, puedes volver a obtenerlo:

    Método: POST

    URL: http://127.0.0.1:8000/api/auth/token/

    Headers:

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
    "username": "vendedor_test_005",
    "password": "otra_password_segura123"
    }

    Enviar y Verificar: Recibirás un 200 OK con el token.
    RESPUESTA (EJEMPLO): 200 OK, {
                                  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1Mzk1MTkxNiwiaWF0IjoxNzUzODY1NTE2LCJqdGkiOiI1NWRmMGYxNjQ2ZGU0NWMxYTc4MDEyYjA5NGUzOTg0YSIsInVzZXJfaWQiOjExfQ.MLSENiG2ZjeF9JTvY-8yEADkTQWIOm26fe0jVweOg1g",
                                  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzODY1ODE2LCJpYXQiOjE3NTM4NjU1MTYsImp0aSI6IjhmYmZiN2RlMTg3MTRlYzA4MzI4YjJlNDZiZTlhOWVhIiwidXNlcl9pZCI6MTF9._6zSCrGpZUPgGvIehjXxVbOQ5zwgQyYLb3VAh1OuJRo"
                                 }

Paso 2: Gestión de Tiendas (Rol Vendedor)

Necesitarás al menos una tienda asociada a tu vendedor_test_005 para poder crear categorías y productos.

2.1. Crear una Tienda

    Método: POST

    URL: http://127.0.0.1:8000/api/tiendas/tiendas/

    Headers:

        Authorization: Token {{seller_auth_token}} (o pega tu token de vendedor directamente)

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
    "nombre": "Mi Nueva Tienda de Electrónica",
    "slug": "mi-nueva-tienda-electronica",
    "descripcion": "Especialistas en gadgets y componentes electrónicos de última generación.",
    "logo": null,
    "banner": null,
    "direccion": "Calle Ficticia 500, Viña del Mar",
    "telefono": "+56987654321",
    "email_contacto": "contacto@electronica-ana.com"
    }

    Enviar y Verificar: 201 Created. Anote el id de la tienda creada (ej: ID_TIENDA).
    RESPUESTA: 201 Created, {
    "id": 1,
    "nombre": "Mi Nueva Tienda de Electrónica",
    "slug": "mi-nueva-tienda-de-electronica",
    "descripcion": "Especialistas en gadgets y componentes electrónicos de última generación.",
    "direccion": "Calle Ficticia 500, Viña del Mar",
    "latitud": null,
    "longitud": null,
    "telefono": "+56987654321",
    "email": null,
    "url": null,
    "horario_atencion": null,
    "logo": null,
    "fecha_creacion": "2025-07-30T01:41:10.058614-04:00",
    "activo": true,
    "radios_envio": []
    }

2.2. Listar Tiendas (para verificar IDs)

    Método: GET

    URL: {{base_url}}/api/tiendas/tiendas/

    Headers: Authorization: Token {{seller_auth_token}}

    Enviar y Verificar: 200 OK con la lista de tus tiendas.

Paso 3: Gestión de Productos - Categorías y Subcategorías (Rol Vendedor)

Ahora crearemos la estructura de categorías y subcategorías. Recuerda usar el ID_TIENDA que obtuviste en el paso anterior.

3.1. Crear Categorías

    Método: POST

    URL: {{base_url}}/api/productos/categorias/

    Headers:

        Authorization: Token {{seller_auth_token}}

        Content-Type: application/json

    Body (raw - JSON):
    JSON

{"nombre": "Electrónica", "tienda": ID_TIENDA}

    Enviar y Verificar: 201 Created. Anote el id (ej: ID_ELECTRONICA)

Repetir para "Ropa":
JSON

    {"nombre": "Ropa", "tienda": ID_TIENDA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_ROPA)

3.2. Listar Categorías (para verificar IDs)

    Método: GET

    URL: {{base_url}}/api/productos/categorias/

    Headers: None (o sin Authorization)

    Enviar y Verificar: 200 OK con la lista de categorías.

3.3. Crear Subcategorías

    Subcategoría "Telefonía" (Electrónica)

        Método: POST

        URL: {{base_url}}/api/productos/subcategorias/

        Headers: Authorization: Token {{seller_auth_token}}, Content-Type: application/json

        Body: {"nombre": "Telefonía", "categoria": ID_ELECTRONICA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_TELEFONIA)

    Subcategoría "Audio" (Electrónica)

        Método: POST

        URL: {{base_url}}/api/productos/subcategorias/

        Headers: Authorization: Token {{seller_auth_token}}, Content-Type: application/json

        Body: {"nombre": "Audio", "categoria": ID_ELECTRONICA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_AUDIO)

    Subcategoría "Computación" (Electrónica)

        Método: POST

        URL: {{base_url}}/api/productos/subcategorias/

        Headers: Authorization: Token {{seller_auth_token}}, Content-Type: application/json

        Body: {"nombre": "Computación", "categoria": ID_ELECTRONICA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_COMPUTACION)

    Subcategoría "Hombre" (Ropa)

        Método: POST

        URL: {{base_url}}/api/productos/subcategorias/

        Headers: Authorization: Token {{seller_auth_token}}, Content-Type: application/json

        Body: {"nombre": "Hombre", "categoria": ID_ROPA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_HOMBRE)

    Subcategoría "Mujer" (Ropa)

        Método: POST

        URL: {{base_url}}/api/productos/subcategorias/

        Headers: Authorization: Token {{seller_auth_token}}, Content-Type: application/json

        Body: {"nombre": "Mujer", "categoria": ID_ROPA}

        Enviar y Verificar: 201 Created. Anote el id (ej: ID_MUJER)

3.4. Listar Subcategorías (para verificar IDs)

    Método: GET

    URL: {{base_url}}/api/productos/subcategorias/

    Headers: None (o sin Authorization)

    Enviar y Verificar: 200 OK con la lista de subcategorías.

Paso 4: Crear Productos (Mínimo 10-15)

Ahora, con todos los IDs de categorías y subcategorías, puedes crear los productos. Repite este proceso 10-15 veces, cambiando los datos y la subcategoria para cada producto. Asegúrate de usar ID_TIENDA en todas.

    Método: POST

    URL: {{base_url}}/api/productos/productos/

    Headers:

        Authorization: Token {{seller_auth_token}}

        Content-Type: application/json

    Ejemplos de Body (elige las subcategorías y crea varios por cada una):

        Producto para "Telefonía" (ej: tu Smartphone original, si no lo tienes)
        JSON

{
    "nombre": "Smartphone XYZ Pro",
    "descripcion": "Un smartphone de última generación.",
    "precio_efectivo": "79990", "precio_tarjeta": "82990", "stock": 25,
    "imagen": null, "disponible": true,
    "tienda": ID_TIENDA, "subcategoria": ID_TELEFONIA 
}

Producto para "Audio" (ej: Auriculares)
JSON

{
    "nombre": "Auriculares Bluetooth Premium",
    "descripcion": "Auriculares con cancelación de ruido activa.",
    "precio_efectivo": "120000", "precio_tarjeta": "125000", "stock": 50,
    "imagen": null, "disponible": true,
    "tienda": ID_TIENDA, "subcategoria": ID_AUDIO
}

Producto para "Computación" (ej: Teclado)
JSON

{
    "nombre": "Teclado Mecánico RGB",
    "descripcion": "Teclado gaming con switches Cherry MX.",
    "precio_efectivo": "85000", "precio_tarjeta": "89000", "stock": 30,
    "imagen": null, "disponible": true,
    "tienda": ID_TIENDA, "subcategoria": ID_COMPUTACION
}

Producto para "Hombre" (ej: Camisa)
JSON

{
    "nombre": "Camisa Casual Hombre",
    "descripcion": "Camisa de algodón 100%.",
    "precio_efectivo": "25000", "precio_tarjeta": "26500", "stock": 70,
    "imagen": null, "disponible": true,
    "tienda": ID_TIENDA, "subcategoria": ID_HOMBRE
}

Producto para "Mujer" (ej: Vestido)
JSON

        {
            "nombre": "Vestido Verano Mujer",
            "descripcion": "Vestido floral ligero ideal para el verano.",
            "precio_efectivo": "35000", "precio_tarjeta": "37000", "stock": 60,
            "imagen": null, "disponible": true,
            "tienda": ID_TIENDA, "subcategoria": ID_MUJER
        }

    Enviar y Verificar: 201 Created para cada uno. Anote los id de al menos 3-4 productos diferentes para usarlos en las pruebas del carrito.

4.1. Listar Productos (para verificar IDs y disponibilidad)

    Método: GET

    URL: {{base_url}}/api/productos/productos/

    Headers: None (o sin Authorization)

    Enviar y Verificar: 200 OK con la lista de todos tus productos. Asegúrate de que todos los productos que creaste aparecen aquí.

    Apéndice: Guía Completa de Postman para tu Plataforma Multitienda

Resumen Detallado del Progreso de la APIHemos construido y probado las funcionalidades centrales de tu plataforma multitienda, abarcando la gestión de usuarios (vendedores y compradores) y un sistema de carrito de compras robusto para ambos tipos de usuarios.
1. Creación de Usuarios Vendedores y TiendasObjetivo: Establecer un usuario con perfil de vendedor y una tienda asociada.
Creación de Usuario Vendedor:Postman: POST a /api/usuarios/register/ con username, email, password.Verificación: 201 Created.Obtención de Tokens JWT (Vendedor):Postman: POST a /api/token/ con username y password.Verificación: 200 OK con access y refresh tokens. Se copió el access token.Creación de Perfil de Vendedor:Postman: POST a /api/usuarios/perfiles-vendedor/ con Authorization: Bearer <ACCESS_TOKEN_VENDEDOR> y datos del perfil.Verificación: 201 Created.Creación de Tienda:Postman: POST a /api/tiendas/ con Authorization: Bearer <ACCESS_TOKEN_VENDEDOR> y datos de la tienda (nombre, dirección, etc.), incluyendo el id del vendedor (que se asigna automáticamente en la vista).Verificación: 201 Created. Se obtuvo el id de la tienda.Corrección de Permisos en tiendas/views.py:Cambio Clave: Se ajustó get_permissions en TiendaViewSet para usar IsSeller para operaciones de escritura y AllowAny para lectura, asegurando que solo vendedores puedan crear/modificar tiendas, pero cualquiera pueda verlas.2. Gestión de Productos, Categorías y SubcategoríasObjetivo: Permitir a los vendedores organizar y añadir productos a sus tiendas.Creación de Categoría:Postman: POST a /api/productos/categorias/ (inicialmente /api/productos/categorias/ debido a la redundancia de URL, luego corregido a /api/categorias/) con Authorization: Bearer <ACCESS_TOKEN_VENDEDOR> y nombre, descripcion, tienda_id.Verificación: 201 Created. Se obtuvo el id de la categoría.Creación de Subcategoría:Postman: POST a /api/productos/subcategorias/ (inicialmente /api/productos/subcategorias/, luego corregido a /api/subcategorias/) con Authorization: Bearer <ACCESS_TOKEN_VENDEDOR> y nombre, descripcion, categoria_id.Verificación: 201 Created. Se obtuvo el id de la subcategoría.Creación de Producto:Postman: POST a /api/productos/ (inicialmente /api/productos/productos/, luego corregido a /api/productos/) con Authorization: Bearer <ACCESS_TOKEN_VENDEDOR> y datos del producto (nombre, precio, stock, tienda_id, subcategoria_id).Verificación: 201 Created, incluyendo la URL de la imagen_qr_generado. Se validó la generación automática del QR y el uso de unique_together para ItemCarrito.Corrección de URLs en core_multitienda/urls.py:Cambio Clave: Se modificaron las líneas path('api/productos/', include('productos.urls')) y path('api/carritos/', include('carritos.urls')) a path('api/', include('productos.urls')) y path('api/', include('carritos.urls')) respectivamente.Impacto: Eliminó la redundancia en las URLs (/api/productos/productos/ se convirtió en /api/productos/, etc.), haciendo las rutas más limpias.Verificación: Se repitió el proceso de creación de Categoría, Subcategoría y Producto con las nuevas URLs, confirmando 201 Created en cada caso.Corrección de Permisos en productos/views.py:Cambio Clave: Se ajustó permission_classes en CategoriaViewSet, SubCategoriaViewSet, y ProductoViewSet de [IsAuthenticatedOrReadOnly, IsSeller] a [IsAuthenticatedOrReadOnly].Impacto: Permitió que las operaciones GET (lectura) de productos, categorías y subcategorías fueran de acceso público (sin requerir autenticación), mientras que las operaciones de escritura siguen siendo validadas por la lógica interna de perform_create (que verifica si el usuario es un vendedor).Verificación: GET a /api/productos/7/ sin Authorization header resultó en 200 OK.3. Gestión de Carritos de Compras (Compradores Registrados e Invitados)Objetivo: Implementar un sistema de carrito flexible que soporte usuarios autenticados y no autenticados, incluyendo adición, actualización, eliminación y fusión de ítems.Correcciones en carritos/models.py, carritos/serializers.py, carritos/views.py, carritos/urls.py:Modelos: Confirmación de unique_together = ('carrito', 'producto') en ItemCarrito para evitar duplicados y sumar cantidades.Serializadores: Ajustes menores en decimal_places y read_only_fields para mayor precisión y claridad.Vistas:Implementación de la lógica para mi_carrito (obtener/crear carrito para autenticados o invitados).Manejo de guest_id para usuarios no autenticados.Lógica para fusionar_carrito (mover ítems de carrito de invitado a carrito de usuario registrado y eliminar el de invitado).Cambio Clave: Adición del método retrieve en CarritoViewSet para GET /api/carritos/{id}/.Cambio Clave: Refactorización de la clase de permiso IsItemCartOwner a IsCartOwner, heredando de BasePermission y con has_permission/has_object_permission para manejar correctamente tanto usuarios autenticados como invitados (verificando guest_id).Cambio Clave: Lógica en ItemCarritoViewSet.update para eliminar un ItemCarrito si la cantidad se actualiza a 0 o menos.URLs: Ajuste final en core_multitienda/urls.py para carritos a path('api/', include('carritos.urls')) para eliminar redundancia.Flujo para Comprador Registrado:Creación de Usuario: POST a /api/usuarios/register/ (201 Created).Obtención de Tokens: POST a /api/token/ (200 OK).Obtener/Crear Carrito: GET a /api/carritos/mi_carrito/ con Authorization (201 Created). Se obtuvo el id del carrito (ej. 3).Añadir Producto: POST a /api/carritos/3/items/ con producto_id y cantidad (201 Created).Aumentar Cantidad (mismo producto): POST a /api/carritos/3/items/ con el mismo producto_id y nueva cantidad (200 OK, cantidad total actualizada).Cambiar Cantidad (PATCH): PATCH a /api/carritos/3/items/<ID_ITEM_CARRITO>/ con cantidad: 1 (200 OK).Eliminar Producto (Cantidad = 0): PATCH a /api/carritos/3/items/<ID_ITEM_CARRITO>/ con cantidad: 0 (204 No Content).Verificar Carrito Vacío: GET a /api/carritos/3/ (200 OK, items: []).Flujo para Comprador Invitado:Generar guest_id: Se usó un UUID (ej. 84243a17-bcb9-42e3-b806-6d923d31dbab).Obtener/Crear Carrito: GET a /api/carritos/mi_carrito/?guest_id=<GUEST_ID> (sin Authorization) (200 OK o 201 Created). Se obtuvo el id del carrito (ej. 4).Añadir Producto: POST a /api/carritos/4/items/ con producto_id, cantidad, y guest_id en el body (sin Authorization) (201 Created).Cambiar Cantidad (PATCH): PATCH a /api/carritos/4/items/<ID_ITEM_CARRITO>/ con cantidad: 1 y guest_id en el body (200 OK).Eliminar Producto (Cantidad = 0): PATCH a /api/carritos/4/items/<ID_ITEM_CARRITO>/ con cantidad: 0 y guest_id en el body (204 No Content).Verificar Carrito Vacío: GET a /api/carritos/4/ con guest_id en query params (200 OK, items: []).Flujo de Fusión de Carritos:Añadir Producto a Carrito Invitado: POST a /api/carritos/4/items/ (sin Authorization) para tener contenido (201 Created).Obtener Token de Comprador Registrado: POST a /api/token/ (200 OK).Fusionar Carrito: POST a /api/carritos/fusionar_carrito/ con Authorization: Bearer <ACCESS_TOKEN_REGISTRADO> y guest_id en el body (200 OK, carrito registrado con ítems fusionados).Verificar Eliminación de Carrito Invitado: GET a /api/carritos/4/ con guest_id en query params (sin Authorization) (404 Not Found).Este resumen abarca los principales hitos y las verificaciones que hemos realizado para asegurar la funcionalidad de tu API.