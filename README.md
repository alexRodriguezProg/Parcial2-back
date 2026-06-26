# Food Store — Backend API

API REST + WebSocket del sistema Food Store, desarrollado con FastAPI + SQLModel + PostgreSQL.

## Stack

- **FastAPI** 0.115 — Framework REST + WebSocket
- **SQLModel** — ORM + schemas Pydantic
- **PostgreSQL** — Base de datos
- **PyJWT + bcrypt** — Autenticación con cookies HttpOnly
- **MercadoPago** — Pasarela de pagos (API REST directa)
- **Cloudinary** — Gestión de imágenes

---

## Setup

> **Importante:** usar Python **3.12 o anterior**. Con Python 3.13 falla `psycopg2-binary` (requiere Microsoft Visual C++ Build Tools en Windows).

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd Parcial2-back
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus credenciales:

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Conexión a PostgreSQL (`postgresql://user:pass@localhost:5432/foodstore_db`) |
| `SECRET_KEY` | Clave para firmar JWT (mín. 32 caracteres) |
| `ALGORITHM` | Algoritmo JWT (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del token (ej. `60`) |
| `FRONTEND_STORE_URL` | URL del frontend store (con HTTPS: `https://localhost:5173`) |
| `FRONTEND_ADMIN_URL` | URL del frontend admin (`http://localhost:5174`) |
| `MP_ACCESS_TOKEN` | Access Token de Mercado Pago |
| `MP_PUBLIC_KEY` | Public Key de Mercado Pago |
| `MP_NOTIFICATION_URL` | Webhook público (ngrok) para notificaciones IPN de MP |
| `CLOUDINARY_CLOUD_NAME` | Cloud name de Cloudinary |
| `CLOUDINARY_API_KEY` | API Key de Cloudinary |
| `CLOUDINARY_API_SECRET` | API Secret de Cloudinary |

### 3. Crear la base de datos

```sql
CREATE DATABASE foodstore_db;
```

### 4. Ejecutar seed

```bash
python -m app.seed
```

Carga: roles (admin, cliente, stock, pedidos), estados de pedido (pendiente, confirmado, preparando, enviado, entregado, cancelado), formas de pago (efectivo, mercadopago, transferencia), 6 productos con ingredientes y 2 categorías.

### 5. Correr el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Disponible en `http://localhost:8000`. Documentación interactiva en `/docs`.

---

## Endpoints de la API

Todas las rutas (excepto WebSocket) tienen prefijo `/api/v1`.

### Auth — `/api/v1/auth`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/register` | Registrar nuevo usuario |
| POST | `/auth/login` | Iniciar sesión (setea cookie HttpOnly) |
| POST | `/auth/logout` | Cerrar sesión (elimina cookie) |
| GET | `/auth/me` | Obtener usuario autenticado |

La autenticación usa **cookies HttpOnly** con JWT. El frontend debe enviar `withCredentials: true`.

### Productos — `/api/v1/productos`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/productos/` | Listar productos (filtros: `categoria_id`, `disponible`, `search`) |
| GET | `/productos/{id}` | Detalle de producto con ingredientes |
| POST | `/productos/` | Crear producto |
| PUT | `/productos/{id}` | Actualizar producto |
| PATCH | `/productos/{id}/disponibilidad` | Cambiar disponibilidad |
| PATCH | `/productos/{id}/imagenes` | Actualizar imágenes (recibe `imagenes_url: string[]`) |
| DELETE | `/productos/{id}` | Eliminar producto |
| POST | `/productos/{id}/ingredientes` | Asignar ingrediente |
| DELETE | `/productos/{id}/ingredientes/{ing_id}` | Quitar ingrediente |
| POST | `/productos/{id}/categorias` | Asignar categoría |
| DELETE | `/productos/{id}/categorias/{cat_id}` | Quitar categoría |

### Categorías — `/api/v1/categorias`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/categorias/` | Listar categorías (filtros: `parent_id`, `include_subcategorias`) |
| GET | `/categorias/flat` | Lista plana de categorías |
| GET | `/categorias/{id}` | Detalle |
| POST | `/categorias/` | Crear |
| PUT | `/categorias/{id}` | Actualizar |
| DELETE | `/categorias/{id}` | Eliminar |

### Ingredientes — `/api/v1/ingredientes`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ingredientes/` | Listar ingredientes |
| GET | `/ingredientes/{id}` | Detalle |
| POST | `/ingredientes/` | Crear |
| PUT | `/ingredientes/{id}` | Actualizar |
| DELETE | `/ingredientes/{id}` | Eliminar |

### Pedidos — `/api/v1/pedidos`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pedidos/` | Listar pedidos (filtros: `skip`, `limit`, `estado_codigo`, `search`) |
| GET | `/pedidos/{id}` | Detalle del pedido con historial |
| POST | `/pedidos/` | Crear pedido (recibe `items` + `forma_pago_codigo`) |
| PATCH | `/pedidos/{id}/estado` | Cambiar estado del pedido |
| GET | `/pedidos/estados` | Listar estados disponibles |
| GET | `/pedidos/formas-pago` | Listar formas de pago disponibles |
| GET | `/pedidos/{id}/historial` | Historial de cambios de estado |

### Pagos — `/api/v1/pagos`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/pagos/crear/{id}` | Crear preferencia de pago en Mercado Pago |
| POST | `/pagos/webhook` | Webhook IPN de notificaciones MP |
| POST | `/pagos/verify/{pedido_id}` | Verificación post-pago (fallback si no llegó el webhook) |
| GET | `/pagos/{id}` | Estado del pago |

### Direcciones — `/api/v1/direcciones`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/direcciones/` | Listar direcciones del usuario |
| GET | `/direcciones/{id}` | Detalle |
| POST | `/direcciones/` | Crear |
| PUT | `/direcciones/{id}` | Actualizar |
| PATCH | `/direcciones/{id}/principal` | Marcar como principal |
| DELETE | `/direcciones/{id}` | Eliminar |

### Admin — `/api/v1/admin`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/admin/usuarios` | Listar usuarios (filtros: `skip`, `limit`, `rol_codigo`) |
| GET | `/admin/usuarios/{id}` | Detalle de usuario |
| PUT | `/admin/usuarios/{id}` | Actualizar usuario |
| DELETE | `/admin/usuarios/{id}` | Eliminar usuario |
| POST | `/admin/usuarios/{id}/roles` | Asignar rol |
| DELETE | `/admin/usuarios/{id}/roles/{rol}` | Quitar rol |
| GET | `/admin/roles` | Listar roles |

### Uploads — `/api/v1/uploads`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/uploads/imagen` | Subir imagen a Cloudinary (multipart, solo ADMIN) |
| DELETE | `/uploads/imagen/{public_id}` | Eliminar imagen de Cloudinary por public_id (solo ADMIN) |

### Estadísticas — `/api/v1/estadisticas`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/estadisticas/resumen` | KPIs: ventas hoy, ticket promedio, pedidos activos, ingresos del mes |
| GET | `/estadisticas/ventas` | Ventas por período (`desde`, `hasta`, `agrupacion: day/week/month`) |
| GET | `/estadisticas/productos-top` | Top productos por ingresos |
| GET | `/estadisticas/pedidos-por-estado` | Cantidad de pedidos por estado actual |
| GET | `/estadisticas/ingresos` | Ingresos por forma de pago (solo pagos approved) |

---

## WebSocket

| Ruta | Descripción |
|------|-------------|
| `/ws/pedidos/{id}?token={jwt}` | Tracking en tiempo real de un pedido específico |
| `/ws/admin/pedidos?token={jwt}` | Escucha global de todos los pedidos (admin / pedidos) |

- Autenticación vía token JWT en query param.
- El frontend se conecta **directamente** a `ws://localhost:8000` (no pasa por el proxy de Vite).
- Los mensajes broadcastan cambios de estado del pedido.

---

## Mercado Pago

- La preferencia de pago se crea con `requests.post` directo a la API de MP (no se usa el SDK oficial por un bug con `auto_return`).
- `back_urls` usan HTTPS obligatoriamente (`https://localhost:5173/pedidos/{id}`).
- `auto_return: "all"` redirige automáticamente al frontend cuando el pago se aprueba o rechaza.
- `binary_mode: True` fuerza estados `approved` / `rejected` sin estados intermedios.

### Flujo de pago

1. El frontend llama a `POST /pagos/crear/{pedido_id}` → recibe `init_point`.
2. Redirige al usuario a MP.
3. MP redirige al frontend vía `back_urls.success`.
4. El frontend llama a `POST /pagos/verify/{pedido_id}` con el `mp_payment_id` que MP envía en la URL.
5. El backend consulta MP, actualiza el estado del pedido y hace broadcast por WebSocket (`pago_verificado`).
6. Como respaldo, el webhook IPN (`POST /pagos/webhook`) también procesa el pago si el verify falla.

### ngrok — Túnel para notificaciones IPN

MP necesita una URL pública para enviar notificaciones de pago. En desarrollo local se usa **ngrok**:

```bash
# 1. Instalar ngrok
winget install ngrok

# 2. Configurar authtoken (sacarlo de https://dashboard.ngrok.com)
ngrok config add-authtoken <tu-token>

# 3. Iniciar túnel
ngrok http http://localhost:8000

# 4. Copiar la URL generada (ej: https://xxxx.ngrok-free.dev)
# 5. Setear en .env:
MP_NOTIFICATION_URL=https://xxxx.ngrok-free.dev/api/v1/pagos/webhook
```

---

## Tests

```bash
pytest -v
```

Requiere base de datos de test configurada.

---

## Credenciales por defecto (seed)

| Rol | Email | Contraseña |
|-----|-------|------------|
| Admin | `admin@foodstore.com` | `Admin1234!` |
| Cliente | `cliente@foodstore.com` | `Cliente1234!` |

---

## Documentación del código

Todas las funciones de routers, services y core tienen docstrings en español documentando su propósito.
