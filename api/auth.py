from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect  # <-- ¡CORRECCIÓN CLAVE!
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from datetime import datetime # Para la fecha de registro

# Configura el contexto de hasheo
# Usamos Argon2 porque bcrypt estaba dando problemas en Render
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter()

@router.post("/api/auth/login")
async def api_login(correo: str = Form(), contrasena: str = Form()):
    """
    Ruta de Login, actualizada a tu esquema 'Usuario'
    """
    print(f"🔹 API: Intento de login para: {correo}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión con la base de datos"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Usamos los nombres correctos: 'Usuario', 'email', 'password_hash'
        cursor.execute(
            "SELECT id_usuario, rol, password_hash, activo FROM Usuario WHERE email = %s", 
            (correo,)
        )
        usuario = cursor.fetchone()
        
        # 2. Verificar si el usuario existe y está activo
        if not usuario:
            print("❌ API: Email no encontrado")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)
        
        if not usuario["activo"]:
            print("❌ API: Cuenta inactiva")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Esta cuenta ha sido desactivada"}, status_code=403)

        # 3. Verificamos la contraseña (usando 'password_hash')
        if not pwd_context.verify(contrasena, usuario["password_hash"]):
            print("❌ API: Contraseña incorrecta")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)
        
        # 4. ¡Éxito!
        cursor.close(); conn.close()
        
        print(f"✅ API: Login exitoso para {usuario['id_usuario']}")
        return JSONResponse({
            "id_usuario": usuario['id_usuario'],
            "rol": usuario['rol'] # Tu BD usa 'Jugador', 'Administrador'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Login): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  RUTA PARA REGISTRO (Corregida para tu Esquema)
# ==========================================================
@router.post("/api/auth/register")
async def api_register(
    correo: str = Form(),
    curp: str = Form(), 
    nombre: str = Form(),
    apellido: str = Form(),
    contrasena: str = Form()
):
    """
    Ruta de Registro, actualizada a tu esquema 'Usuario' y 'Saldo'
    """
    print(f"🔹 API: Intento de registro para: {correo}")
    conn = None
    cursor = None
    
    try:
        # 1. Hashear la contraseña
        hashed_password = pwd_context.hash(contrasena)
        
        # 2. Conectarse a la BD
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 3. PASO 1: Insertar en la tabla 'Usuario'
        cursor.execute(
            """
            INSERT INTO Usuario (nombre, apellido, curp, email, password_hash, rol, fecha_registro, activo)
            VALUES (%s, %s, %s, %s, %s, 'Jugador', %s, true)
            RETURNING id_usuario
            """,
            (nombre, apellido, curp, correo, hashed_password, datetime.now())
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
        
        print(f"✅ API: Registro exitoso para {correo}, ID: {new_user_id}")
        return JSONResponse({"success": True, "message": "Usuario registrado exitosamente"})

    except psycopg2.errors.UniqueViolation as e:
        if conn: conn.rollback()
        print(f"❌ API: Conflicto de datos (email o curp ya existen): {e}")
        return JSONResponse({"error": "El correo electrónico o la CURP ya están registrados."}, status_code=409)
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Register): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  RUTA: RECUPERAR CONTRASEÑA (SIMULACIÓN)
# ==========================================================
@router.post("/api/auth/forgot-password")
async def api_forgot_password(correo: str = Form()):
    """
    Ruta para manejar la solicitud de "Olvidé mi contraseña".
    Llamada por: forgot_password.html
    """
    print(f"🔹 API: Solicitud de recuperación de contraseña para: {correo}")
    
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"message": "Si este correo está registrado, recibirás un enlace de recuperación."})
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Buscamos al usuario
        cursor.execute("SELECT id_usuario FROM Usuario WHERE email = %s AND activo = true", (correo,))
        usuario = cursor.fetchone()
        
        # 2. SIMULACIÓN
        if usuario:
            token_simulado = "TOKEN_SEGURO_GENERADO_AQUI_12345"
            print(f"✅ API: SIMULACIÓN - Enviando email de reseteo a {correo} con token: {token_simulado}")
        else:
            print(f"❌ API: Solicitud de reseteo para email no existente o inactivo: {correo}")

        # 3. RESPUESTA GENÉRICA
        return JSONResponse({"success": True, "message": "Si este correo está registrado en nuestro sistema, recibirás un enlace para recuperar tu contraseña."})

    except Exception as e:
        print(f"🚨 API ERROR (Forgot Password): {e}")
        return JSONResponse({"message": "Si este correo está registrado, recibirás un enlace de recuperación."})
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
