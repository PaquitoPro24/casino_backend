# Blackjack Royal - PostgreSQL + JWT + App Inventor

Aplicación de Blackjack con backend FastAPI, autenticación JWT, y compatibilidad con App Inventor.

## 🚀 Características

- ✅ **Backend FastAPI** con autenticación JWT
- ✅ **PostgreSQL** con SQLAlchemy ORM
- ✅ **Autenticación Híbrida**: Soporta cookies (App Inventor) y headers Authorization (web)
- ✅ **Seguridad**: Argon2 para hashing de contraseñas
- ✅ **Compatible con App Inventor**: Login automático vía query params
- ✅ **Persistencia**: Saldo sincronizado con PostgreSQL en cada jugada

## 📋 Requisitos

- Python 3.11+
- PostgreSQL (Neon.tech o similar)
- Cuenta en Render.com para despliegue

## 🛠️ Configuración Local

### 1. Clonar el Repositorio

```bash
git clone <tu-repositorio>
cd blackjack-web
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia `.env.example` a `.env` y configura:

```env
DATABASE_URL=postgresql://usuario:password@host/database?sslmode=require
JWT_SECRET=tu-secret-key-super-segura
```

**Generar JWT_SECRET seguro:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Crear Tablas en PostgreSQL

Ejecuta el siguiente script SQL en tu base de datos:

```sql
-- Tabla de roles
CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(30) UNIQUE NOT NULL,
    descripcion TEXT
);

-- Insertar rol por defecto
INSERT INTO rol (nombre, descripcion) VALUES ('Jugador', 'Usuario jugador estándar');

-- Tabla de usuarios
CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INTEGER NOT NULL REFERENCES rol(id_rol),
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    curp VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de saldos
CREATE TABLE saldo (
    id_saldo SERIAL PRIMARY KEY,
    id_usuario INTEGER UNIQUE NOT NULL REFERENCES usuario(id_usuario),
    saldo_actual NUMERIC(10, 2) NOT NULL DEFAULT 0,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Crear Usuario de Prueba

```python
from auth import get_password_hash
import psycopg2
import os

# Conectar a PostgreSQL
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Hashear contraseña con Argon2
password_hash = get_password_hash("password123")

# Insertar usuario
cur.execute("""
    INSERT INTO usuario (id_rol, nombre, apellido, curp, email, password_hash)
    VALUES (1, 'Test', 'User', 'TEST123456', 'test@example.com', %s)
    RETURNING id_usuario
""", (password_hash,))
user_id = cur.fetchone()[0]

# Crear saldo inicial
cur.execute("""
    INSERT INTO saldo (id_usuario, saldo_actual)
    VALUES (%s, 500.00)
""", (user_id,))

conn.commit()
conn.close()
print(f"✅ Usuario creado: test@example.com con saldo $500")
```

### 7. Ejecutar Servidor Local

```bash
uvicorn app:app --reload
```

La aplicación estará disponible en: `http://localhost:8000`

## 🌐 Uso desde App Inventor

### Login Automático

Desde App Inventor, usa el componente `WebViewer` con la siguiente URL:

```
https://tu-app.onrender.com/?user_email=test@example.com
```

Esto creará automáticamente un token JWT y lo guardará en una cookie, permitiendo que el usuario juegue sin necesidad de login manual.

## 🚀 Despliegue en Render

### 1. Crear Cuenta en Render

Visita [render.com](https://render.com) y crea una cuenta.

### 2. Crear PostgreSQL Database

1. Dashboard → **New** → **PostgreSQL**
2. Anota la **DATABASE_URL** generada automáticamente

### 3. Crear Web Service

1. Dashboard → **New** → **Web Service**
2. Conecta tu repositorio de GitHub
3. Configuración:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### 4. Configurar Variables de Entorno

En el panel de **Environment** del Web Service, agrega:

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | *(Se crea automáticamente al agregar PostgreSQL)* |
| `JWT_SECRET` | *(Genera una clave segura con `secrets.token_urlsafe(32)`)* |

### 5. Crear Tablas

Conecta a tu PostgreSQL de Render con un cliente (pgAdmin, DBeaver, etc.) y ejecuta el script SQL de creación de tablas.

### 6. Deploy

Render desplegará automáticamente cuando detecte cambios en GitHub.

## 📁 Estructura del Proyecto

```
blackjack-web/
├── app.py                 # Aplicación FastAPI principal
├── database.py            # Configuración SQLAlchemy
├── models.py              # Modelos ORM (Usuario, Rol, Saldo)
├── auth.py                # Autenticación JWT y Argon2
├── requirements.txt       # Dependencias Python
├── runtime.txt            # Versión de Python
├── Procfile              # Comando de inicio para Render
├── .env.example          # Ejemplo de variables de entorno
├── static/
│   ├── index.html        # Frontend del juego
│   ├── app.js            # Lógica del juego
│   ├── db-integration.js # Integración con BD
│   ├── style.css         # Estilos
│   └── security.css      # Protección frontend
└── README.md             # Este archivo
```

## 🔒 Seguridad

- **Argon2**: Hashing seguro de contraseñas
- **JWT**: Tokens con expiración de 7 días
- **HTTPS Only**: Las cookies requieren conexión segura
- **CORS**: Configurado para permitir App Inventor
- **Frontend Protection**: Bloqueo de DevTools y copiar/pegar

## 🎮 Endpoints de la API

### Autenticación

- `POST /api/auth/login` - Login con email/password
- `GET /?user_email=...` - Login automático desde App Inventor

### Juego

- `GET /api/state` - Obtener estado actual del juego
- `GET /api/saldo` - Obtener saldo del usuario
- `POST /api/bet` - Hacer apuesta
- `POST /api/clear_bet` - Borrar apuesta
- `POST /api/deal` - Repartir cartas
- `POST /api/hit` - Pedir carta
- `POST /api/stand` - Mantenerse
- `POST /api/double` - Doblar apuesta
- `POST /api/new_round` - Nueva ronda

## 📝 Notas

### Estado del Juego

El estado del juego se mantiene en memoria del servidor (`game_states = {}`). Esto funciona bien para desarrollo y servidores single-process. En producción con múltiples workers, considera usar:

- **Redis** para almacenamiento de sesiones distribuidas
- **PostgreSQL** para persistir estado del juego en tablas

### Migración desde Flask

Se creó un backup del archivo anterior en `app_flask_backup.py`. La app anterior usaba sesiones de Flask; la nueva usa JWT + almacenamiento en memoria.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

## 📄 Licencia

MIT License - Siéntete libre de usar este código para tus proyectos.
