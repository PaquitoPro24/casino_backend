from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext

router = APIRouter()

# Configurar contexto de hasheo
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

@router.post("/login")
async def login(
    correo: str = Form(...),
    contrasena: str = Form(...)
):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT u.id_usuario, u.email, u.password_hash, 
                   r.nombre AS rol, u.activo
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE u.email = %s
            """,
            (correo,)
        )
        user = cursor.fetchone()

        if not user:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)

        if not pwd_context.verify(contrasena, user['password_hash']):
            return JSONResponse({"error": "Contraseña incorrecta"}, status_code=401)

        if not user['activo']:
            return JSONResponse({"error": "Cuenta inactiva"}, status_code=403)

        # --- AQUI VIENE LA SOLUCIÓN ---
        response = JSONResponse({
            "id_usuario": user["id_usuario"],
            "rol": user["rol"],
            "message": "Inicio de sesión correcto"
        })

        # Cookies NECESARIAS para /agente/*
        response.set_cookie(
            key="userId",
            value=str(user["id_usuario"]),
            path="/",
            httponly=False,
            samesite="lax"
        )

        response.set_cookie(
            key="rol",
            value=user["rol"],
            path="/",
            httponly=False,
            samesite="lax"
        )

        return response
        # -------------------------------

    except Exception as e:
        print(f"🚨 Error en login (router): {e}")
        return JSONResponse({"error": "Error interno del servidor"}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
