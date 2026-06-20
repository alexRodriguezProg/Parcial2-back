# 🍔 Food Store — Backend API

Backend REST + WebSocket del sistema Food Store, desarrollado con FastAPI + SQLModel + PostgreSQL.

## Stack

- **FastAPI** 0.115 — Framework REST + WebSocket
- **SQLModel** — ORM + schemas Pydantic
- **PostgreSQL** — Base de datos
- **JWT** — Autenticación
- **MercadoPago** — Pasarela de pagos
- **Cloudinary** — Gestión de imágenes

---

## Setup

⚠️ **Importante:** usar Python **3.12 o anterior**. Con Python 3.13 falla la instalación de `psycopg2-binary` (requiere compilar con Microsoft Visual C++ Build Tools en Windows). Verificá tu versión con `python --version` antes de crear el entorno virtual.

### 1. Clonar el repositorio

```bash
git clone https://github.com/alexRodriguezProg/Parcial2-back.git
cd Parcial2-back
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus credenciales de PostgreSQL, MercadoPago y Cloudinary.

### 4. Crear la base de datos

En pgAdmin o psql:

```sql
CREATE DATABASE foodstore_db;
```

### 5. Correr el seed

```bash
python -m app.seed
```

Carga roles, estados, formas de pago,