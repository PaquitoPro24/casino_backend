from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/disponibles/{id_usuario}")
async def bonos_usuario(id_usuario: int):
    """
    Obtiene los bonos de un usuario
    NOTA: El endpoint principal está en /api/bonos/activos/{id_usuario}
    Este es un router alternativo/redundante
    """
    print(f"🔹 Router: Obteniendo bonos del usuario {id_usuario}")
    conn = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consultar con nombres correctos de tablas
        cursor.execute(
            """
            SELECT b.nombre_bono, b.descripcion, ub.estado 
            FROM Usuario_Bono ub
            JOIN Bono b ON b.id_bono = ub.id_bono
            WHERE ub.id_usuario = %s
            """,
            (id_usuario,)
        )
        
        bonos = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"bonos": bonos})
        
    except Exception as e:
        print(f"🚨 Error al obtener bonos: {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
