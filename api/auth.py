from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import db_connect  # Tu archivo db_connect.py
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from datetime import datetime # Para la fecha de registro

# Configura el contexto de hasheo
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
#  NUEVA RUTA PARA REGISTRO (Corregida para tu Esquema)
# ==========================================================
@router.post("/api/auth/register")
async def api_register(
    correo: str = Form(),
    curp: str = Form(), # <-- ¡Añadido de nuevo!
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
        # Usamos los nombres de tu tabla: 'Usuario', 'nombre', 'apellido', etc.
        # Usamos el rol 'Jugador' (de tu CHECK) y 'activo = true'
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
        # Error específico si el email o curp ya existen (si los tienes como UNIQUE en tu BD)
        if conn: conn.rollback() # Revertir la transacción
        print(f"❌ API: Conflicto de datos (email o curp ya existen): {e}")
        # Tu schema solo marca 'email' como UNIQUE, así que es el error más probable
        return JSONResponse({"error": "El correo electrónico ya está registrado."}, status_code=409)
        
    except Exception as e:
        if conn: conn.rollback() # Revertir en caso de cualquier otro error
        print(f"🚨 API ERROR (Register): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
