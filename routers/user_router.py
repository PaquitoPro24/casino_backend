from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/{id_usuario}")
async def obtener_usuario(id_usuario: int):
    """
    Obtiene información de un usuario
    NOTA: El endpoint principal está en /api/user/{id_usuario}
    Este es un router alternativo/redundante
    """
    print(f"🔹 Router: Obteniendo info del usuario {id_usuario}")
    conn = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consultar con nombres correctos de tablas y columnas
        cursor.execute(
            """
            SELECT 
                u.id_usuario,
                u.nombre,
                u.apellido,
                u.email,
                r.nombre as rol,
                u.activo,
                s.saldo_actual
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            LEFT JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.id_usuario = %s
            """,
            (id_usuario,)
        )
        
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)
        
        # Convertir decimal a float
        if usuario.get('saldo_actual'):
            usuario['saldo_actual'] = float(usuario['saldo_actual'])
        
        return JSONResponse(usuario)
        
    except Exception as e:
        print(f"🚨 Error al obtener usuario: {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
