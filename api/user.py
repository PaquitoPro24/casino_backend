from fastapi import APIRouter
from fastapi.responses import JSONResponse
import db_connect  # Importa tu conector
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/api/user/{id_usuario}")
async def api_get_user_info(id_usuario: int):
    """
    Esta es la ruta que tu account-cartera-historial.html llama.
    """
    print(f"🔹 API: Pidiendo info para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # ⚠️ ¡ATENCIÓN! Cambia 'usuarios', 'nombre' y 'saldo_total'
        # por los nombres EXACTOS de tu tabla y columnas en Neon.
        cursor.execute(
            "SELECT nombre, saldo_total FROM usuarios WHERE id_usuario = %s", 
            (id_usuario,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)
        
        # Devolvemos el JSON que el HTML espera
        return JSONResponse({
            "nombre": usuario['nombre'],
            "saldo": usuario['saldo_total'] # Tu HTML espera 'saldo'
        })

    except Exception as e:
        print(f"🚨 API ERROR: {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
