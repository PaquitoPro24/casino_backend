from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

router = APIRouter()

# ==========================================================
#  CREAR NUEVO TICKET DE SOPORTE
# ==========================================================
@router.post("/api/support/tickets/create")
async def api_create_ticket(
    id_usuario: int = Form(),
    asunto: str = Form(),  # Viene del <select>
    mensaje: str = Form()  # Viene del <textarea>
):
    """
    Ruta para crear un nuevo ticket en la tabla 'Soporte'
    Llamada por: support-tickets-nuevo.html
    """
    print(f"🔹 API: Creando ticket para usuario: {id_usuario}, Asunto: {asunto}")
    
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()

        # Insertamos en la tabla 'Soporte' con estado 'Abierto'
        cursor.execute(
            """
            INSERT INTO Soporte (id_usuario, asunto, mensaje, estado, fecha_creacion)
            VALUES (%s, %s, %s, 'Abierto', %s)
            """,
            (id_usuario, asunto, mensaje, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ API: Ticket creado para {id_usuario}")
        return JSONResponse({"success": True, "message": "Ticket de soporte enviado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Crear Ticket): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  OBTENER TICKETS (ACTIVOS E HISTORIAL)
# ==========================================================

@router.get("/api/support/tickets/active/{id_usuario}")
async def api_get_active_tickets(id_usuario: int):
    """
    Ruta para obtener tickets 'Abiertos' o 'Asignados'
    Llamada por: support-tickets-activo.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscamos tickets que NO estén 'Cerrados'
        cursor.execute(
            """
            SELECT id_ticket, asunto, estado, fecha_creacion
            FROM Soporte
            WHERE id_usuario = %s AND estado != 'Cerrado'
            ORDER BY fecha_creacion DESC
            """,
            (id_usuario,)
        )
        tickets = cursor.fetchall()
        cursor.close()
        return JSONResponse({"tickets": tickets})

    except Exception as e:
        print(f"🚨 API ERROR (Tickets Activos): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


@router.get("/api/support/tickets/history/{id_usuario}")
async def api_get_ticket_history(id_usuario: int):
    """
    Ruta para obtener tickets 'Cerrados'
    Llamada por: support-tickets-historial.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscamos tickets que SÍ estén 'Cerrados'
        cursor.execute(
            """
            SELECT id_ticket, asunto, estado, fecha_creacion
            FROM Soporte
            WHERE id_usuario = %s AND estado = 'Cerrado'
            ORDER BY fecha_creacion DESC
            """,
            (id_usuario,)
        )
        tickets = cursor.fetchall()
        cursor.close()
        return JSONResponse({"tickets": tickets})

    except Exception as e:
        print(f"🚨 API ERROR (Historial Tickets): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
