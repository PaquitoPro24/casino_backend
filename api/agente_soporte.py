from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

router = APIRouter()

# ==========================================================
#  DASHBOARD DEL AGENTE - ESTADÍSTICAS
# ==========================================================
@router.get("/api/agente/dashboard/{id_agente}")
async def api_get_agent_dashboard(id_agente: int):
    """
    Obtiene estadísticas del dashboard para el agente de soporte
    Usando solo la tabla Soporte
    """
    print(f"🔹 API Agente: Dashboard para agente {id_agente}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Tickets pendientes (Abiertos, sin asignar a ningún agente)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Soporte
            WHERE estado = 'Abierto' AND id_agente IS NULL
        """)
        tickets_pendientes = cursor.fetchone()['total']
        
        # 2. Tickets asignados al agente (activos - no cerrados)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Soporte
            WHERE id_agente = %s AND estado != 'Cerrado'
        """, (id_agente,))
        mis_tickets = cursor.fetchone()['total']
        
        # 3. Tickets cerrados hoy por el agente
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Soporte
            WHERE id_agente = %s 
            AND estado = 'Cerrado'
            AND DATE(fecha_cierre) = CURRENT_DATE
        """, (id_agente,))
        cerrados_hoy = cursor.fetchone()['total']
        
        cursor.close()
        
        return JSONResponse({
            "tickets_pendientes": tickets_pendientes,
            "mis_tickets": mis_tickets,
            "cerrados_hoy": cerrados_hoy
        })

    except Exception as e:
        print(f"🚨 API ERROR (Agent Dashboard): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  LISTAR TODOS LOS TICKETS (PARA AGENTE)
# ==========================================================
@router.get("/api/agente/tickets/all")
async def api_get_all_tickets():
    """
    Obtiene todos los tickets para que el agente pueda verlos
    """
    print("🔹 API Agente: Listando todos los tickets")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener todos los tickets con información del jugador
        cursor.execute("""
            SELECT 
                s.id_ticket,
                s.id_jugador,
                u.nombre as nombre_jugador,
                u.apellido as apellido_jugador,
                s.asunto,
                s.estado,
                s.fecha_creacion,
                s.id_agente,
                CASE WHEN s.id_agente IS NOT NULL THEN 'Asignado' ELSE 'Sin asignar' END as estado_asignacion
            FROM Soporte s
            JOIN Usuario u ON s.id_jugador = u.id_usuario
            ORDER BY 
                CASE WHEN s.estado = 'Abierto' THEN 1
                     WHEN s.estado = 'En Proceso' THEN 2
                     ELSE 3 END,
                s.fecha_creacion DESC
        """)
        
        tickets = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"tickets": tickets})

    except Exception as e:
        print(f"🚨 API ERROR (Listar Tickets): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  LISTAR MIS TICKETS (ASIGNADOS AL AGENTE)
# ==========================================================
@router.get("/api/agente/tickets/mis-tickets/{id_agente}")
async def api_get_my_tickets(id_agente: int):
    """
    Obtiene los tickets asignados a un agente específico
    """
    print(f"🔹 API Agente: Tickets del agente {id_agente}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s.id_ticket,
                s.id_jugador,
                u.nombre as nombre_jugador,
                u.apellido as apellido_jugador,
                s.asunto,
                s.estado,
                s.fecha_creacion
            FROM Soporte s
            JOIN Usuario u ON s.id_jugador = u.id_usuario
            WHERE s.id_agente = %s AND s.estado != 'Cerrado'
            ORDER BY s.fecha_creacion DESC
        """, (id_agente,))
        
        tickets = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"tickets": tickets})

    except Exception as e:
        print(f"🚨 API ERROR (Mis Tickets): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  ASIGNAR TICKET A AGENTE
# ==========================================================
@router.post("/api/agente/tickets/asignar")
async def api_assign_ticket(
    id_ticket: int = Form(),
    id_agente: int = Form()
):
    """
    Asigna un ticket a un agente y cambia el estado a 'En Proceso'
    """
    print(f"🔹 API Agente: Asignando ticket {id_ticket} al agente {id_agente}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Actualizar el ticket con el id_agente y cambiar estado
        cursor.execute("""
            UPDATE Soporte
            SET id_agente = %s, estado = 'En Proceso'
            WHERE id_ticket = %s
        """, (id_agente, id_ticket))
        
        conn.commit()
        
        print(f"✅ Ticket {id_ticket} asignado al agente {id_agente}")
        return JSONResponse({"success": True, "message": "Ticket asignado correctamente"})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Asignar Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ==========================================================
#  OBTENER DETALLE DE UN TICKET
# ==========================================================
@router.get("/api/agente/tickets/detalle/{id_ticket}")
async def api_get_ticket_detail(id_ticket: int):
    """
    Obtiene el detalle completo de un ticket
    """
    print(f"🔹 API Agente: Detalle del ticket {id_ticket}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s.id_ticket,
                s.id_jugador,
                u.nombre as nombre_jugador,
                u.apellido as apellido_jugador,
                u.email as email_jugador,
                s.asunto,
                s.mensaje,
                s.estado,
                s.fecha_creacion,
                s.fecha_cierre,
                s.id_agente
            FROM Soporte s
            JOIN Usuario u ON s.id_jugador = u.id_usuario
            WHERE s.id_ticket = %s
        """, (id_ticket,))
        
        ticket = cursor.fetchone()
        cursor.close()
        
        if not ticket:
            return JSONResponse({"error": "Ticket no encontrado"}, status_code=404)
        
        return JSONResponse(ticket)

    except Exception as e:
        print(f"🚨 API ERROR (Detalle Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  CERRAR TICKET
# ==========================================================
@router.post("/api/agente/tickets/cerrar")
async def api_close_ticket(id_ticket: int = Form()):
    """
    Cierra un ticket y registra la fecha de cierre
    """
    print(f"🔹 API Agente: Cerrando ticket {id_ticket}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Soporte
            SET estado = 'Cerrado', fecha_cierre = %s
            WHERE id_ticket = %s
        """, (datetime.now(), id_ticket))
        
        conn.commit()
        
        print(f"✅ Ticket {id_ticket} cerrado")
        return JSONResponse({"success": True, "message": "Ticket cerrado correctamente"})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Cerrar Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ==========================================================
#  REABRIR TICKET
# ==========================================================
@router.post("/api/agente/tickets/reabrir")
async def api_reopen_ticket(id_ticket: int = Form()):
    """
    Reabre un ticket cerrado
    """
    print(f"🔹 API Agente: Reabriendo ticket {id_ticket}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Soporte
            SET estado = 'En Proceso', fecha_cierre = NULL
            WHERE id_ticket = %s
        """, (id_ticket,))
        
        conn.commit()
        
        print(f"✅ Ticket {id_ticket} reabierto")
        return JSONResponse({"success": True, "message": "Ticket reabierto correctamente"})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Reabrir Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
