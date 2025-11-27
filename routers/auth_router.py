from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection

router = APIRouter()

@router.post("/login")
async def login(
    correo: str = Form(...),
    contrasena: str = Form(...)
):
    """
    Inicia sesión de usuario y devuelve su rol para redirección.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 🔍 Verificar si existe el usuario
        cursor.execute("SELECT id_usuario, correo, contrasena, rol FROM usuarios WHERE correo = %s", (correo,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)

        # 🔑 Validar contraseña
        if user["contrasena"] != contrasena:
            return JSONResponse({"error": "Contraseña incorrecta"}, status_code=401)

        # ✅ Si todo está correcto
        return JSONResponse({
            "id_usuario": user["id_usuario"],
            "rol": user["rol"],
            "message": "Inicio de sesión correcto"
        })

    except Exception as e:
        print("⚠️ Error en login:", e)
        return JSONResponse({"error": "Error interno del servidor"}, status_code=500)