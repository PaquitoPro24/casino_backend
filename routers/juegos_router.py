from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/listar")
async def listar_juegos():
    """
    Lista todos los juegos activos
    NOTA: El endpoint principal está en /api/admin/games
    Este es un router alternativo/redundante
    """
    print("🔹 Router: Listando juegos activos")
    conn = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consultar con nombres correctos (Juego con columna activo BOOLEAN)
        cursor.execute(
            "SELECT id_juego, nombre, descripcion, rtp, min_apuesta, max_apuesta, activo FROM Juego WHERE activo = true"
        )
        
        juegos = cursor.fetchall()
        cursor.close()
        
        # Convertir decimales a float
        for juego in juegos:
            if juego.get('rtp'):
                juego['rtp'] = float(juego['rtp'])
            if juego.get('min_apuesta'):
                juego['min_apuesta'] = float(juego['min_apuesta'])
            if juego.get('max_apuesta'):
                juego['max_apuesta'] = float(juego['max_apuesta'])
        
        return JSONResponse({"juegos": juegos})
        
    except Exception as e:
        print(f"🚨 Error al listar juegos: {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
