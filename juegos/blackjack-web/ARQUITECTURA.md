# Arquitectura del Proyecto - Blackjack Web

## Separación de Responsabilidades

Este proyecto sigue el principio de **separación de responsabilidades (Separation of Concerns)**:

### 🎮 Aplicación de Blackjack (Este Proyecto)
**Responsabilidad**: Solo manejar el juego y sincronizar saldo

**Funcionalidades**:
- Lógica del juego de Blackjack
- Leer saldo del usuario desde PostgreSQL
- Actualizar saldo después de cada ronda
- Mantener sesión del juego

**Endpoints**:
- `GET /?user_id=email` - Cargar juego con usuario
- `GET /api/login?user_id=email` - Iniciar sesión (opcional)
- `GET /api/state` - Obtener estado del juego
- `POST /api/bet` - Hacer apuesta
- `POST /api/hit` - Pedir carta
- `POST /api/stand` - Plantarse
- `POST /api/double` - Doblar apuesta
- `POST /api/deal` - Repartir cartas
- `POST /api/new_round` - Nueva ronda

---

### 🔐 Servicio de Autenticación (Separado)
**Responsabilidad**: Registro y login de usuarios

**Debería estar en otro proyecto/servicio con**:
- `POST /api/registrar` - Crear nuevo usuario
- `POST /api/login` - Verificar credenciales
- `POST /api/logout` - Cerrar sesión
- `GET /api/perfil` - Obtener datos del usuario

**Nota**: Las funciones `registrar_usuario_nuevo()` y `verificar_usuario()` en `db_config.py` están disponibles pero no se usan en este proyecto. Puedes usarlas para crear un servicio de autenticación separado.

---

## Flujo Recomendado

```
1. App Inventor
   ↓
2. Servicio de Autenticación (separado)
   - Registro
   - Login
   - Obtiene email del usuario
   ↓
3. App Inventor guarda email en TinyDB
   ↓
4. Blackjack Web (este proyecto)
   - Recibe user_id (email) por URL
   - Carga saldo desde PostgreSQL
   - Juega
   - Actualiza saldo en PostgreSQL
```

---

## Ventajas de Esta Arquitectura

### ✅ Modularidad
- Cada servicio tiene una responsabilidad clara
- Fácil de mantener y actualizar

### ✅ Escalabilidad
- Puedes escalar el juego y la autenticación independientemente
- Puedes tener múltiples juegos usando el mismo servicio de autenticación

### ✅ Seguridad
- El juego no maneja contraseñas
- La autenticación está aislada

### ✅ Reutilización
- El servicio de autenticación puede usarse para otros juegos
- El juego puede usarse con diferentes sistemas de autenticación

---

## Cómo Usar

### Opción 1: Solo Juego (Actual)
Si ya tienes un sistema de autenticación:

```
https://blackjack-web-z4fm.onrender.com/?user_id=usuario@email.com
```

El juego asume que el usuario ya está autenticado y solo sincroniza el saldo.

### Opción 2: Con Servicio de Autenticación Separado
Crea otro proyecto Flask para autenticación:

```python
# auth_service.py
from db_config import registrar_usuario_nuevo, verificar_usuario

@app.route("/api/registrar", methods=["POST"])
def registrar():
    # ... código de registro

@app.route("/api/login", methods=["POST"])
def login():
    # ... código de login
```

Despliega en otra URL:
- Autenticación: `https://casino-auth.onrender.com`
- Blackjack: `https://blackjack-web-z4fm.onrender.com`

---

## Configuración Actual

### Variables de Entorno Necesarias
```
DATABASE_URL=postgresql://...  # Conexión a Neon.tech
SECRET_KEY=...                  # Clave secreta para sesiones
```

### Base de Datos
Usa las tablas:
- `Usuario` - Datos del usuario
- `Saldo` - Saldo actual del usuario

---

## Próximos Pasos Recomendados

1. **Crear servicio de autenticación separado** (opcional)
2. **Usar el juego actual** con el `user_id` desde App Inventor
3. **Escalar** cada servicio según necesidad
