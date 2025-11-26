from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

router = APIRouter()

# ==========================================================
#  OBTENER BONOS DISPONIBLES (Para 'account-bonos.html')
# ==========================================================
@router.get("/api/bonos/disponibles/{id_usuario}")
async def api_get_available_bonos(id_usuario: int):
    """
    Obtiene bonos que están activos Y que el usuario AÚN NO TIENE.
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Este SQL usa un LEFT JOIN para encontrar bonos en la tabla 'Bono'
        # que NO tengan una entrada correspondiente en 'Usuario_Bono' para ESE usuario.
        cursor.execute(
            """
            SELECT b.id_bono, b.nombre_bono, b.tipo, b.descripcion
            FROM Bono b
            LEFT JOIN Usuario_Bono ub ON b.id_bono = ub.id_bono AND ub.id_usuario = %s
            WHERE 
                b.activo = true 
                AND (b.fecha_expiracion IS NULL OR b.fecha_expiracion > NOW())
                AND ub.id_bono IS NULL -- La clave: solo los que NO tiene
            """,
            (id_usuario,)
        )
        bonos = cursor.fetchall()
        cursor.close()
        return JSONResponse({"bonos": bonos})

    except Exception as e:
        print(f"🚨 API ERROR (Bonos Disponibles): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  RECLAMAR UN BONO (Para 'account-bonos.html')
# ==========================================================
@router.post("/api/bonos/reclamar")
async def api_claim_bono(
    id_usuario: int = Form(),
    id_bono: int = Form()
):
    """
    Crea una nueva entrada en la tabla 'Usuario_Bono'
    """
    print(f"🔹 API: Usuario {id_usuario} intenta reclamar bono {id_bono}")
    conn = None
    cursor = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Insertamos el bono para el usuario con estado 'Activo'
        cursor.execute(
            """
            INSERT INTO Usuario_Bono (id_usuario, id_bono, fecha_adquisicion, estado, progreso)
            VALUES (%s, %s, %s, 'Activo', 0.00)
            """,
            (id_usuario, id_bono, datetime.now())
        )
        conn.commit()
        
        print(f"✅ API: Bono {id_bono} reclamado por {id_usuario}")
        return JSONResponse({"success": True, "message": "Bono reclamado con éxito."})

    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        print(f"❌ API: Usuario {id_usuario} ya tiene el bono {id_bono}")
        return JSONResponse({"error": "Ya has reclamado este bono."}, status_code=409)
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Reclamar Bono): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  OBTENER BONOS ACTIVOS (Para 'account-bonos-activos.html')
# ==========================================================
@router.get("/api/bonos/activos/{id_usuario}")
async def api_get_active_bonos(id_usuario: int):
    """
    Obtiene los bonos que el usuario SÍ tiene y están 'Activos'
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT b.nombre_bono, ub.fecha_adquisicion, ub.progreso
            FROM Usuario_Bono ub
            JOIN Bono b ON ub.id_bono = b.id_bono
            WHERE ub.id_usuario = %s AND ub.estado = 'Activo'
            ORDER BY ub.fecha_adquisicion DESC
            """,
            (id_usuario,)
        )
        bonos = cursor.fetchall()
        cursor.close()
        
        # Convertir datetime a ISO format para JSON
        for bono in bonos:
            if bono.get('fecha_adquisicion'):
                bono['fecha_adquisicion'] = bono['fecha_adquisicion'].isoformat()
            if bono.get('progreso'):
                bono['progreso'] = float(bono['progreso'])
        
        return JSONResponse({"bonos": bonos})

    except Exception as e:
        print(f"🚨 API ERROR (Bonos Activos): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  OBTENER BONOS HISTORIAL (Para 'account-bonos-historial.html')
# ==========================================================
@router.get("/api/bonos/historial/{id_usuario}")
async def api_get_bonus_history(id_usuario: int):
    """
    Obtiene los bonos que el usuario tiene y están 'Usado' o 'Expirado'
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT b.nombre_bono, ub.fecha_adquisicion, ub.estado
            FROM Usuario_Bono ub
            JOIN Bono b ON ub.id_bono = b.id_bono
            WHERE ub.id_usuario = %s AND ub.estado IN ('Usado', 'Expirado')
            ORDER BY ub.fecha_adquisicion DESC
            """,
            (id_usuario,)
        )
        bonos = cursor.fetchall()
        cursor.close()
        
        # Convertir datetime a ISO format para JSON
        for bono in bonos:
            if bono.get('fecha_adquisicion'):
                bono['fecha_adquisicion'] = bono['fecha_adquisicion'].isoformat()
        
        return JSONResponse({"bonos": bonos})

    except Exception as e:
        print(f"🚨 API ERROR (Historial Bonos): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
