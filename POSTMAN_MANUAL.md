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

    URL: {{base_url}}/api/auth/registro/

    Headers:

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
        "username": "usuario_comprador_1",
        "email": "comprador1@example.com",
        "password": "mi_password_seguro_123",
        "password2": "mi_password_seguro_123",
        "is_customer": true,
        "is_seller": false
    }

    Enviar y Verificar: Deberías recibir un 201 Created con los datos del usuario y un token. Guarda este token. Puedes copiarlo y pegarlo en la variable auth_token de tu entorno de Postman para el comprador.

1.2. Crear un Usuario (Vendedor)

    Método: POST

    URL: {{base_url}}/api/auth/registro/

    Headers:

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
        "username": "usuario_vendedor_1",
        "email": "vendedor1@example.com",
        "password": "mi_password_seguro_456",
        "password2": "mi_password_seguro_456",
        "is_customer": false,
        "is_seller": true,
        "razon_social": "Mi Empresa de Ventas S.A.",
        "rut": "12345678-9",
        "direccion": "Calle Falsa 123, Ciudad"
    }

    Enviar y Verificar: Deberías recibir un 201 Created con los datos del vendedor y su token. Guarda este token en otra variable de entorno (ej. seller_auth_token) o simplemente tenlo a mano.

1.3. Iniciar Sesión (para obtener un token si no lo tienes)

Si por alguna razón pierdes un token, puedes volver a obtenerlo:

    Método: POST

    URL: {{base_url}}/api/auth/login/

    Headers:

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
        "username": "usuario_vendedor_1",
        "password": "mi_password_seguro_456"
    }

    Enviar y Verificar: Recibirás un 200 OK con el token.

Paso 2: Gestión de Tiendas (Rol Vendedor)

Necesitarás al menos una tienda asociada a tu usuario_vendedor_1 para poder crear categorías y productos.

2.1. Crear una Tienda

    Método: POST

    URL: {{base_url}}/api/tiendas/tiendas/

    Headers:

        Authorization: Token {{seller_auth_token}} (o pega tu token de vendedor directamente)

        Content-Type: application/json

    Body (raw - JSON):
    JSON

    {
        "nombre": "Mi Tienda Central",
        "descripcion": "Tienda principal de electrónica y accesorios.",
        "direccion": "Avenida Siempre Viva 742"
    }

    Enviar y Verificar: 201 Created. Anote el id de la tienda creada (ej: ID_TIENDA).

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