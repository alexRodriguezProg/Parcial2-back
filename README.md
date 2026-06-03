# Backend - Parcial 2 API

## Descripción del proyecto

Backend desarrollado con **FastAPI** para una API de gestión de usuarios, autenticación, roles, categorías, ingredientes, productos, pedidos, direcciones de entrega, estados de pedido y formas de pago.

El proyecto utiliza **PostgreSQL** como base de datos y **SQLModel** como ORM. Además, expone documentación automática mediante **Swagger/OpenAPI**.

---

# Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

* Python 3.12 o superior.
* PostgreSQL.
* pip (gestor de paquetes de Python).

---

# Instalación

Clonar el repositorio y posicionarse dentro de la carpeta del backend:

```bash
cd backend
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Dependencias principales:

* fastapi==0.115.0
* uvicorn[standard]==0.30.6
* sqlmodel==0.0.21
* psycopg2-binary==2.9.9
* python-dotenv==1.0.1
* PyJWT==2.9.0
* bcrypt==4.2.0
* python-multipart==0.0.12
* pydantic[email]==2.9.2
* pydantic-settings==2.5.2

---

# Configuración del entorno

El repositorio incluye un archivo:

```text
.env.example
```

Crear una copia llamada:

```text
.env
```

### Windows

```powershell
copy .env.example .env
```

### Linux / macOS

```bash
cp .env.example .env
```

---

# Configuración de PostgreSQL

Crear una base de datos PostgreSQL llamada:

```sql
CREATE DATABASE parcial2_db;
```

Luego editar el archivo `.env` y configurar la conexión según la instalación local de PostgreSQL.

Ejemplo:

```env
DATABASE_URL=postgresql://<usuario>:<contraseña>@localhost:<puerto>/parcial2_db
SECRET_KEY=clave-super-secreta-minimo-32-caracteres-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_STORE_URL=http://localhost:5173
FRONTEND_ADMIN_URL=http://localhost:5174
```

### Variables obligatorias

* DATABASE_URL
* SECRET_KEY

### Variables opcionales

* ALGORITHM (por defecto: HS256)
* ACCESS_TOKEN_EXPIRE_MINUTES (por defecto: 30)
* FRONTEND_STORE_URL (por defecto: http://localhost:5173)
* FRONTEND_ADMIN_URL (por defecto: http://localhost:5174)

---

# Inicialización de la base de datos

El proyecto incluye un seed que:

* Crea las tablas necesarias.
* Inserta datos iniciales.

Para ejecutarlo:

```bash
python -m app.seed
```

El seed carga:

* Roles.
* Estados de pedido.
* Formas de pago.
* Categorías.
* Ingredientes.
* Productos.
* Usuario administrador.

Si el proceso finaliza correctamente se mostrará un mensaje similar a:

```text
✅ Seed completado!
```

---

# Usuario administrador inicial

El seed crea automáticamente el siguiente usuario administrador:

```text
Email: admin@parcial2.com
Password: Admin1234!
```

---

# Iniciar el servidor

Una vez ejecutado el seed, iniciar la aplicación:

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en:

```text
http://127.0.0.1:8000
```

---

# Documentación Swagger

Con el servidor iniciado, acceder a:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Orden de ejecución recomendado

Para una instalación desde cero:

1. Instalar PostgreSQL.
2. Crear la base de datos `parcial2_db`.
3. Crear el archivo `.env` a partir de `.env.example`.
4. Configurar `DATABASE_URL` según la instalación local.
5. Instalar dependencias:

```bash
pip install -r requirements.txt
```

6. Ejecutar el seed:

```bash
python -m app.seed
```

7. Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

8. Acceder a Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# Solución de problemas

## Error: DATABASE_URL o SECRET_KEY faltantes

Verificar que exista el archivo:

```text
.env
```

y que contenga todas las variables requeridas.

---

## Error de conexión a PostgreSQL

Verificar:

* Que PostgreSQL esté en ejecución.
* Que el usuario y contraseña sean correctos.
* Que el puerto configurado coincida con el de la instalación local.
* Que la base de datos `parcial2_db` exista.

---

## Las tablas no existen

Ejecutar nuevamente:

```bash
python -m app.seed
```

El seed se encarga de crear las tablas e insertar los datos iniciales.

---

## No se puede iniciar sesión como administrador

Asegurarse de haber ejecutado correctamente el seed.

Credenciales iniciales:

```text
admin@parcial2.com
Admin1234!
```

# Verificación de funcionamiento

Una vez iniciado el servidor, abrir en el navegador:

http://127.0.0.1:8000/

La respuesta esperada es:

```json
{
  "message": "API funcionando"
}
```

Si se obtiene esta respuesta, significa que la API se encuentra ejecutándose correctamente.