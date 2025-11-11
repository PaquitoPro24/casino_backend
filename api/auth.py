from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
import db_connect  # Importa tu conector
import psycopg2
from psycopg2.extras import RealDictCursor
# Importa la librería para hashear contraseñas (la necesitarás)
# from passlib.context import CryptContext

# (Opcional, pero recomendado para contraseñas)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Creamos un "mini-FastAPI"
router = APIRouter()

@router.post("/api/auth/login")
async def api_login(correo: str = Form(), contrasena: str = Form()):
    """
    Esta es la ruta de API que tu login.html llama.
    """
    print(f"🔹 API: Intento de login para: {correo}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión con la base de datos"}, status_code=500)
        
        # RealDictCursor nos devuelve diccionarios, es más fácil
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # ⚠️ ¡ATENCIÓN! Cambia 'usuarios', 'email' y 'contrasena_hash'
        # por los nombres EXACTOS de tu tabla y columnas en Neon.
        cursor.execute(
            "SELECT id_usuario, rol FROM usuarios WHERE email = %s AND contrasena_hash = %s", 
            (correo, contrasena) # ¡IMPORTANTE! Debes comparar contraseñas hasheadas, no texto plano.
        )
        
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            print("❌ API: Credenciales incorrectas")
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)

        # Devolvemos el JSON que tu login.html espera
        print(f"✅ API: Login exitoso para {usuario['id_usuario']}")
        return JSONResponse({
            "id_usuario": usuario['id_usuario'],
            "rol": usuario['rol']
        })

    except Exception as e:
        print(f"🚨 API ERROR: {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()

# -----------------------------------------------------------------
# PRÓXIMO PASO: Aquí crearíamos la ruta para registrar
# -----------------------------------------------------------------
# @router.post("/api/auth/register")
# async def api_register(...):
#     # ... (Lógica para INSERT INTO usuarios ...)
#     pass
