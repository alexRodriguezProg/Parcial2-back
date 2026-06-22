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
cd Global-back
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
| `SECRET_KEY` | Clave para firmar JWT |
| `JWT_EXPIRATION_MINUTES` | Minutos de validez del token (ej. `60`) |
| `MP_ACCESS_TOKEN` | Access Token de Mercado Pago (producción) |
| `MP_NOTIFICATION_URL` | URL de webhook para notificaciones MP |
| `MP_PUBLIC_KEY` | Public Key de Mercado Pago |
| `CLOUDINARY_URL` | URL de Cloudinary para imágenes |

### 3. Crear la base de datos

```sql
CREATE DATABASE foodstore_db;
```

### 4. Ejecutar seed

```bash
python -m app.seed
```

Carga: roles (admin, cliente), estados de pedido (pendiente, confirmado, preparando, enviado, entregado, cancelado), formas de pago (efectivo, mercadopago), 6 productos con ingredientes y 2 categorías.

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
| GET | `/productos/` | Listar productos (filtros: `categoria_id`, `disponible`, `q`) |
| GET | `/productos/{id}` | Detalle de producto con ingredientes |
| POST | `/productos/` | Crear producto |
| PUT | `/productos/{id}` | Actualizar producto |
| PATCH | `/productos/{id}/disponibilidad` | Cambiar disponibilidad |
| DELETE | `/productos/{id}` | Eliminar producto |
| POST | `/productos/{id}/ingredientes` | Asignar ingrediente |
| DELETE | `/productos/{id}/ingredientes/{ing_id}` | Quitar ingrediente |

### Categorías — `/api/v1/categorias`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/categorias/` | Árbol de categorías (jerárquico) |
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
| GET | `/pedidos/` | Listar pedidos del usuario autenticado |
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
| POST | `/pagos/webhook` | Webhook de notificaciones MP |
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
| GET | `/admin/usuarios` | Listar usuarios |
| GET | `/admin/usuarios/{id}` | Detalle de usuario |
| PUT | `/admin/usuarios/{id}` | Actualizar usuario |
| DELETE | `/admin/usuarios/{id}` | Eliminar usuario |
| POST | `/admin/usuarios/{id}/roles` | Asignar rol |
| DELETE | `/admin/usuarios/{id}/roles/{rol}` | Quitar rol |
| GET | `/admin/roles` | Listar roles |

### Uploads — `/api/v1/uploads`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/uploads/` | Subir imagen a Cloudinary |

### Estadísticas — `/api/v1/estadisticas`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/estadisticas/` | Dashboard del admin |

---

## WebSocket

| Ruta | Descripción |
|------|-------------|
| `/ws/pedidos/{id}?token={jwt}` | Tracking en tiempo real de un pedido específico |
| `/ws/admin/pedidos?token={jwt}` | Escucha global de todos los pedidos (admin) |

- Autenticación vía token JWT en query param.
- El frontend se conecta **directamente** a `ws://localhost:8000` (no pasa por el proxy de Vite).
- Los mensajes broadcastan cambios de estado del pedido.

---

## Mercado Pago

- La preferencia de pago se crea con `requests.post` directo a la API de MP (no se usa el SDK oficial por un bug con `auto_return`).
- `back_urls` usan HTTPS obligatoriamente (`https://localhost:5173/pedidos/{id}`).
- `auto_return: "approved"` redirige automáticamente al frontend cuando el pago se aprueba.

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
