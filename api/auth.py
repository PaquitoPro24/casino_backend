from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, constr
from app.db import db_connect  # <-- ¡CORRECCIÓN CLAVE!
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from datetime import datetime # Para la fecha de registro

# Configura el contexto de hasheo
# Usamos Argon2 porque bcrypt estaba dando problemas en Render
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter()

# Modelo Pydantic para validar los datos de entrada del login
class UserLogin(BaseModel):
    correo: EmailStr
    contrasena: str

# Modelo Pydantic para validar los datos de entrada del registro
class UserRegister(BaseModel):
    correo: EmailStr
    curp: str # constr(min_length=18, max_length=18) - Relaxed for debugging
    nombre: str
    apellido: str
    contrasena: str

# Modelo Pydantic para la recuperación de contraseña
class ForgotPasswordRequest(BaseModel):
    correo: EmailStr

# Modelo Pydantic para el cambio directo de contraseña
class ResetPasswordRequest(BaseModel):
    correo: EmailStr
    nueva_contrasena: str


@router.post("/login")
async def api_login(user_data: UserLogin):
    """
    Ruta de Login que valida los datos con Pydantic.
    """
    # --- MARCA DE VERSIÓN ---
    # Marca de versión única para este archivo.
    print("✅✅✅ Ejecutando desde 'api/auth.py' - ¡ESTA ES LA VERSIÓN CORRECTA! ✅✅✅")
    print(f"🔹 API: Intento de login para: {user_data.correo}")
    conn = None
    cursor = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            # Si no podemos conectar, es un error crítico del servidor.
            print("🚨 API ERROR (Login): No se pudo obtener conexión a la base de datos.")
            return JSONResponse({"error": "Error interno del servidor"}, status_code=500)
        
        # --- CORRECCIÓN ---
        # Se elimina el argumento `cursor_factory`. Esta configuración se maneja a nivel de conexión (en db_connect.py).
        cursor = conn.cursor()
        
        # 1. Query actualizado para obtener el rol desde la tabla Rol
        cursor.execute(
            """
            SELECT u.id_usuario, u.id_rol, r.nombre as rol_nombre, u.password_hash, u.activo 
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE u.email = %s
            """,
            (user_data.correo,)
        )
        usuario = cursor.fetchone()
        
        # 2. Verificar si el usuario existe y la contraseña es correcta
        if not usuario or not pwd_context.verify(user_data.contrasena, usuario[3]): # Índice 3 para password_hash
            print("❌ API: Credenciales incorrectas (email no encontrado o contraseña no coincide)")
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)
        
        # 3. Verificar si la cuenta está activa (solo si el usuario y la contraseña son válidos)
        if not usuario[4]: # Índice 4 para activo
            print("❌ API: Cuenta inactiva")
            return JSONResponse({"error": "Esta cuenta ha sido desactivada"}, status_code=403)

        # 4. ¡Éxito!
        # 4. ¡Éxito!
        print(f"✅ API: Login exitoso para {usuario[0]} con rol {usuario[2]}")
        response = JSONResponse({
            "id_usuario": usuario[0],  # Índice 0 para id_usuario
            "id_rol": usuario[1],       # Índice 1 para id_rol
            "rol": usuario[2]           # Índice 2 para rol_nombre
        })
        # Set cookie for middleware
        response.set_cookie(key="userId", value=str(usuario[0]), httponly=False) # httponly=False so frontend can read if needed, though middleware reads it from request
        return response

    except Exception as e:
        print(f"🚨 API ERROR (Login): {e}")
        return JSONResponse({"error": "Error interno del servidor"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ==========================================================
#  RUTA PARA REGISTRO (Corregida para tu Esquema)
# ==========================================================
@router.post("/register")
async def api_register(user_data: UserRegister):
    """
    Ruta de Registro que valida los datos con Pydantic.
    """
    print(f"🔹 API: Intento de registro para: {user_data.correo}")
    conn = None
    cursor = None
    
    try:
        # 1. Hashear la contraseña
        hashed_password = pwd_context.hash(user_data.contrasena)
        
        # 2. Conectarse a la BD
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 3. PASO 1: Insertar en la tabla 'Usuario' con id_rol = 1 (Jugador)
        cursor.execute(
            """
            INSERT INTO Usuario (nombre, apellido, curp, email, password_hash, id_rol, fecha_registro, activo)
            VALUES (%s, %s, %s, %s, %s, 1, %s, true)
            RETURNING id_usuario
            """,
            (user_data.nombre, user_data.apellido, user_data.curp, user_data.correo, hashed_password, datetime.now())
        )
        
        # Obtenemos el ID del usuario que acabamos de crear
        new_user_id = cursor.fetchone()[0]
        
        # 4. PASO 2: Insertar en la tabla 'Saldo'
        cursor.execute(
            """
            INSERT INTO Saldo (id_usuario, saldo_actual, ultima_actualizacion)
            VALUES (%s, 0.00, %s)
            """,
            (new_user_id, datetime.now())
        )
        
        # 5. Confirmar la transacción (ambos inserts)
        conn.commit()
        
        print(f"✅ API: Registro exitoso para {user_data.correo}, ID: {new_user_id}")
        return JSONResponse({"success": True, "message": "Usuario registrado exitosamente"})

    except psycopg2.errors.UniqueViolation as e:
        if conn: conn.rollback()
        print(f"❌ API: Conflicto de datos (email o curp ya existen): {e}")
        return JSONResponse({"error": "El correo electrónico o la CURP ya están registrados."}, status_code=409)
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Register): {e}")
        # CORRECCIÓN: Se envía un string simple en lugar del objeto de la excepción.
        return JSONResponse({"error": "Error interno del servidor al intentar registrar."}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  RUTA: RECUPERAR CONTRASEÑA (SIMULACIÓN)
# ==========================================================
@router.post("/forgot-password")
async def api_forgot_password(request_data: ForgotPasswordRequest):
    """
    Ruta para manejar la solicitud de "Olvidé mi contraseña".
    Valida los datos con Pydantic.
    """
    print(f"🔹 API: Solicitud de recuperación de contraseña para: {request_data.correo}")
    
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        # Si la conexión falla, es un error interno. Devolvemos un 500.
        # La respuesta genérica se da al final para no revelar si el email existe.
        if conn is None:
            print("🚨 API ERROR (Forgot Password): No se pudo conectar a la base de datos.")
            return JSONResponse({"error": "Error interno del servidor."}, status_code=500)
        
        # --- CORRECCIÓN FINAL ---
        # Se elimina el argumento `cursor_factory`. Esta configuración se maneja a nivel de conexión.
        cursor = conn.cursor()
        
        # 1. Buscamos al usuario por correo
        cursor.execute("SELECT id_usuario FROM Usuario WHERE email = %s AND activo = true", (request_data.correo,))
        usuario = cursor.fetchone()
        
        # 2. SIMULACIÓN
        if usuario:
            token_simulado = "TOKEN_SEGURO_GENERADO_AQUI_12345"
            print(f"✅ API: SIMULACIÓN - Enviando email de reseteo a {request_data.correo} con token: {token_simulado}")
        else:
            print(f"❌ API: Solicitud de reseteo para email no existente o inactivo: {request_data.correo}")

        # 3. RESPUESTA GENÉRICA
        return JSONResponse({"success": True, "message": "Si este correo está registrado en nuestro sistema, recibirás un enlace para recuperar tu contraseña."})

    except Exception as e:
        print(f"🚨 API ERROR (Forgot Password): {e}")
        return JSONResponse({"error": "Error interno del servidor."}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ==========================================================
#  RUTA: CAMBIO DE CONTRASEÑA DIRECTO (SIN EMAIL)
# ==========================================================
@router.post("/reset-password")
async def api_reset_password(request_data: ResetPasswordRequest):
    """
    Ruta para cambiar la contraseña directamente dado un correo.
    ADVERTENCIA: Esto permite cambiar la contraseña de cualquiera si se conoce el correo.
    """
    print(f"🔹 API: Solicitud de cambio de contraseña directo para: {request_data.correo}")
    
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error interno del servidor."}, status_code=500)
        
        cursor = conn.cursor()
        
        # 1. Verificar si el usuario existe y está activo
        cursor.execute("SELECT id_usuario FROM Usuario WHERE email = %s AND activo = true", (request_data.correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"❌ API: Intento de cambio de contraseña para usuario no encontrado: {request_data.correo}")
            return JSONResponse({"error": "Usuario no encontrado o inactivo."}, status_code=404)
        
        # 2. Hashear la nueva contraseña
        hashed_password = pwd_context.hash(request_data.nueva_contrasena)
        
        # 3. Actualizar la contraseña en la base de datos
        cursor.execute(
            "UPDATE Usuario SET password_hash = %s WHERE email = %s",
            (hashed_password, request_data.correo)
        )
        conn.commit()
        
        print(f"✅ API: Contraseña actualizada exitosamente para {request_data.correo}")
        return JSONResponse({"success": True, "message": "Contraseña actualizada correctamente."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Reset Password): {e}")
        return JSONResponse({"error": "Error interno del servidor al cambiar la contraseña."}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
