from fastapi import APIRouter
from fastapi.responses import JSONResponse
import db_connect  # Tu archivo db_connect.py
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/api/user/{id_usuario}")
async def api_get_user_info(id_usuario: int):
    """
    Ruta para obtener la info básica del usuario (nombre y saldo)
    Llamada por: account-cartera-historial.html
    """
    print(f"🔹 API: Pidiendo info para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Usamos JOIN para obtener datos de 'Usuario' y 'Saldo'
        cursor.execute(
            """
            SELECT
                u.nombre,
                u.rol,
                s.saldo_actual
            FROM
                Usuario u
            JOIN
                Saldo s ON u.id_usuario = s.id_usuario
            WHERE
                u.id_usuario = %s AND u.activo = true
            """, 
            (id_usuario,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return JSONResponse({"error": "Usuario no encontrado o inactivo"}, status_code=404)
        
        # Devolvemos el JSON que el HTML espera
        # (account-cartera-historial.html espera 'nombre' y 'saldo')
        return JSONResponse({
            "nombre": usuario['nombre'],
            "saldo": usuario['saldo_actual'],
            "rol": usuario['rol'] # El HTML no lo usa, pero es bueno tenerlo
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (get_user_info): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
