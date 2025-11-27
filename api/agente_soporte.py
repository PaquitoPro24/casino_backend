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
    """
    print(f"🔹 API Agente: Dashboard para agente {id_agente}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Tickets pendientes (Abiertos, sin asignar)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Soporte s
            WHERE s.estado = 'Abierto'
            AND NOT EXISTS (
                SELECT 1 FROM Ticket_Asignacion ta 
                WHERE ta.id_ticket = s.id_ticket AND ta.activa = TRUE
            )
        """)
        tickets_pendientes = cursor.fetchone()['total']
        
        # 2. Tickets asignados al agente (activos)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Ticket_Asignacion ta
            JOIN Soporte s ON ta.id_ticket = s.id_ticket
            WHERE ta.id_agente = %s 
            AND ta.activa = TRUE
            AND s.estado != 'Cerrado'
        """, (id_agente,))
        mis_tickets = cursor.fetchone()['total']
        
        # 3. Chats en espera
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Chat_Sesion
            WHERE estado = 'Esperando'
        """)
        chats_esperando = cursor.fetchone()['total']
        
        # 4. Mis chats activos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Chat_Sesion
            WHERE id_agente = %s AND estado = 'En curso'
        """, (id_agente,))
        mis_chats = cursor.fetchone()['total']
        
        # 5. Tickets cerrados hoy por este agente
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Soporte s
            JOIN Ticket_Asignacion ta ON s.id_ticket = ta.id_ticket
            WHERE ta.id_agente = %s
            AND s.estado = 'Cerrado'
            AND s.fecha_creacion >= CURRENT_DATE
        """, (id_agente,))
        cerrados_hoy = cursor.fetchone()['total']
        
        cursor.close()
        
        return JSONResponse({
            "tickets_pendientes": tickets_pendientes,
            "mis_tickets": mis_tickets,
            "chats_esperando": chats_esperando,
            "mis_chats": mis_chats,
            "cerrados_hoy": cerrados_hoy
        })
        
    except Exception as e:
        print(f"🚨 API ERROR (Dashboard Agente): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  LISTAR TODOS LOS TICKETS (CON FILTROS)
# ==========================================================
@router.get("/api/agente/tickets")
async def api_get_all_tickets(estado: str = None, asignado: str = None):
    """
    Lista todos los tickets con filtros opcionales
    estado: 'Abierto', 'Asignado', 'Cerrado'
    asignado: 'si', 'no', o None para todos
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consulta base
        query = """
            SELECT 
                s.id_ticket, 
                s.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                s.asunto, 
                s.mensaje,
                s.estado, 
                s.fecha_creacion,
                ta.id_agente,
                CASE 
                    WHEN ta.id_agente IS NOT NULL THEN ag.nombre || ' ' || ag.apellido
                    ELSE NULL
                END as nombre_agente
            FROM Soporte s
            JOIN Usuario u ON s.id_usuario = u.id_usuario
            LEFT JOIN Ticket_Asignacion ta ON s.id_ticket = ta.id_ticket AND ta.activa = TRUE
            LEFT JOIN Usuario ag ON ta.id_agente = ag.id_usuario
            WHERE 1=1
        """
        
        params = []
        
        if estado:
            query += " AND s.estado = %s"
            params.append(estado)
        
        if asignado == 'si':
            query += " AND ta.id_agente IS NOT NULL"
        elif asignado == 'no':
            query += " AND ta.id_agente IS NULL"
        
        query += " ORDER BY s.fecha_creacion DESC LIMIT 100"
        
        cursor.execute(query, params)
        tickets = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"tickets": tickets})
        
    except Exception as e:
        print(f"🚨 API ERROR (Listar Tickets): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  MIS TICKETS ASIGNADOS
# ==========================================================
@router.get("/api/agente/mis-tickets/{id_agente}")
async def api_get_my_tickets(id_agente: int):
    """
    Obtiene los tickets asignados a un agente específico
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s.id_ticket, 
                s.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                s.asunto, 
                s.mensaje,
                s.estado, 
                s.fecha_creacion,
                ta.fecha_asignacion
            FROM Soporte s
            JOIN Ticket_Asignacion ta ON s.id_ticket = ta.id_ticket
            JOIN Usuario u ON s.id_usuario = u.id_usuario
            WHERE ta.id_agente = %s 
            AND ta.activa = TRUE
            AND s.estado != 'Cerrado'
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
@router.post("/api/agente/asignar-ticket")
async def api_assign_ticket(
    id_ticket: int = Form(),
    id_agente: int = Form()
):
    """
    Asigna un ticket a un agente específico
    """
    print(f"🔹 API: Asignando ticket {id_ticket} al agente {id_agente}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Primero, desactivar cualquier asignación previa
        cursor.execute("""
            UPDATE Ticket_Asignacion 
            SET activa = FALSE 
            WHERE id_ticket = %s
        """, (id_ticket,))
        
        # Crear nueva asignación
        cursor.execute("""
            INSERT INTO Ticket_Asignacion (id_ticket, id_agente, fecha_asignacion, activa)
            VALUES (%s, %s, %s, TRUE)
        """, (id_ticket, id_agente, datetime.now()))
        
        # Actualizar estado del ticket a 'Asignado'
        cursor.execute("""
            UPDATE Soporte 
            SET estado = 'Asignado' 
            WHERE id_ticket = %s
        """, (id_ticket,))
        
        conn.commit()
        
        print(f"✅ Ticket {id_ticket} asignado correctamente")
        return JSONResponse({"success": True, "message": "Ticket asignado con éxito"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Asignar Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  OBTENER DETALLES DE TICKET CON RESPUESTAS
# ==========================================================
@router.get("/api/agente/ticket/{id_ticket}")
async def api_get_ticket_details(id_ticket: int):
    """
    Obtiene detalles completos de un ticket incluyendo todas las respuestas
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener info del ticket
        cursor.execute("""
            SELECT 
                s.id_ticket, 
                s.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                u.email,
                s.asunto, 
                s.mensaje,
                s.estado, 
                s.fecha_creacion,
                ta.id_agente,
                CASE 
                    WHEN ta.id_agente IS NOT NULL THEN ag.nombre || ' ' || ag.apellido
                    ELSE NULL
                END as nombre_agente
            FROM Soporte s
            JOIN Usuario u ON s.id_usuario = u.id_usuario
            LEFT JOIN Ticket_Asignacion ta ON s.id_ticket = ta.id_ticket AND ta.activa = TRUE
            LEFT JOIN Usuario ag ON ta.id_agente = ag.id_usuario
            WHERE s.id_ticket = %s
        """, (id_ticket,))
        
        ticket = cursor.fetchone()
        
        if not ticket:
            return JSONResponse({"error": "Ticket no encontrado"}, status_code=404)
        
        # Obtener respuestas
        cursor.execute("""
            SELECT 
                tr.id_respuesta,
                tr.mensaje,
                tr.es_agente,
                tr.fecha_respuesta,
                u.nombre || ' ' || u.apellido as nombre_usuario
            FROM Ticket_Respuesta tr
            JOIN Usuario u ON tr.id_usuario = u.id_usuario
            WHERE tr.id_ticket = %s
            ORDER BY tr.fecha_respuesta ASC
        """, (id_ticket,))
        
        respuestas = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({
            "ticket": ticket,
            "respuestas": respuestas
        })
        
    except Exception as e:
        print(f"🚨 API ERROR (Ticket Details): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  RESPONDER A TICKET
# ==========================================================
@router.post("/api/agente/responder-ticket")
async def api_respond_ticket(
    id_ticket: int = Form(),
    id_agente: int = Form(),
    mensaje: str = Form()
):
    """
    Agrega una respuesta a un ticket
    """
    print(f"🔹 API: Respondiendo ticket {id_ticket}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Insertar respuesta
        cursor.execute("""
            INSERT INTO Ticket_Respuesta (id_ticket, id_usuario, mensaje, es_agente, fecha_respuesta)
            VALUES (%s, %s, %s, TRUE, %s)
        """, (id_ticket, id_agente, mensaje, datetime.now()))
        
        conn.commit()
        
        print(f"✅ Respuesta agregada al ticket {id_ticket}")
        return JSONResponse({"success": True, "message": "Respuesta enviada con éxito"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Responder Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  CERRAR TICKET
# ==========================================================
@router.post("/api/agente/cerrar-ticket")
async def api_close_ticket(id_ticket: int = Form()):
    """
    Cierra un ticket de soporte
    """
    print(f"🔹 API: Cerrando ticket {id_ticket}")
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Soporte 
            SET estado = 'Cerrado' 
            WHERE id_ticket = %s
        """, (id_ticket,))
        
        conn.commit()
        
        print(f"✅ Ticket {id_ticket} cerrado")
        return JSONResponse({"success": True, "message": "Ticket cerrado con éxito"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Cerrar Ticket): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  CHATS - LISTAR CHATS EN ESPERA
# ==========================================================
@router.get("/api/agente/chats-esperando")
async def api_get_waiting_chats():
    """
    Obtiene todos los chats en espera de ser atendidos
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                cs.id_chat,
                cs.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                cs.fecha_inicio
            FROM Chat_Sesion cs
            JOIN Usuario u ON cs.id_usuario = u.id_usuario
            WHERE cs.estado = 'Esperando'
            ORDER BY cs.fecha_inicio ASC
        """)
        
        chats = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"chats": chats})
        
    except Exception as e:
        print(f"🚨 API ERROR (Chats en Espera): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  MIS CHATS ACTIVOS
# ==========================================================
@router.get("/api/agente/mis-chats/{id_agente}")
async def api_get_my_chats(id_agente: int):
    """
    Obtiene los chats activos de un agente
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                cs.id_chat,
                cs.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                cs.fecha_inicio,
                cs.estado
            FROM Chat_Sesion cs
            JOIN Usuario u ON cs.id_usuario = u.id_usuario
            WHERE cs.id_agente = %s AND cs.estado = 'En curso'
            ORDER BY cs.fecha_inicio DESC
        """, (id_agente,))
        
        chats = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"chats": chats})
        
    except Exception as e:
        print(f"🚨 API ERROR (Mis Chats): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  TOMAR CHAT
# ==========================================================
@router.post("/api/agente/tomar-chat")
async def api_take_chat(
    id_chat: int = Form(),
    id_agente: int = Form()
):
    """
    Un agente toma un chat en espera
    """
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Chat_Sesion 
            SET id_agente = %s, estado = 'En curso' 
            WHERE id_chat = %s AND estado = 'Esperando'
        """, (id_agente, id_chat))
        
        conn.commit()
        
        return JSONResponse({"success": True, "message": "Chat tomado con éxito"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Tomar Chat): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  OBTENER MENSAJES DE CHAT
# ==========================================================
@router.get("/api/agente/chat-mensajes/{id_chat}")
async def api_get_chat_messages(id_chat: int):
    """
    Obtiene todos los mensajes de un chat específico
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Info del chat
        cursor.execute("""
            SELECT 
                cs.id_chat,
                cs.id_usuario,
                u.nombre || ' ' || u.apellido as nombre_usuario,
                cs.id_agente,
                cs.estado
            FROM Chat_Sesion cs
            JOIN Usuario u ON cs.id_usuario = u.id_usuario
            WHERE cs.id_chat = %s
        """, (id_chat,))
        
        chat_info = cursor.fetchone()
        
        if not chat_info:
            return JSONResponse({"error": "Chat no encontrado"}, status_code=404)
        
        # Mensajes del chat
        cursor.execute("""
            SELECT 
                cm.id_mensaje,
                cm.mensaje,
                cm.es_agente,
                cm.fecha_mensaje,
                u.nombre || ' ' || u.apellido as nombre_usuario
            FROM Chat_Mensaje cm
            JOIN Usuario u ON cm.id_usuario = u.id_usuario
            WHERE cm.id_chat = %s
            ORDER BY cm.fecha_mensaje ASC
        """, (id_chat,))
        
        mensajes = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({
            "chat": chat_info,
            "mensajes": mensajes
        })
        
    except Exception as e:
        print(f"🚨 API ERROR (Chat Mensajes): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  ENVIAR MENSAJE EN CHAT
# ==========================================================
@router.post("/api/agente/enviar-mensaje-chat")
async def api_send_chat_message(
    id_chat: int = Form(),
    id_agente: int = Form(),
    mensaje: str = Form()
):
    """
    Envía un mensaje en un chat activo
    """
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Chat_Mensaje (id_chat, id_usuario, mensaje, es_agente, fecha_mensaje)
            VALUES (%s, %s, %s, TRUE, %s)
        """, (id_chat, id_agente, mensaje, datetime.now()))
        
        conn.commit()
        
        return JSONResponse({"success": True, "message": "Mensaje enviado"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Enviar Mensaje Chat): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  CERRAR CHAT
# ==========================================================
@router.post("/api/agente/cerrar-chat")
async def api_close_chat(id_chat: int = Form()):
    """
    Cierra una sesión de chat
    """
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Chat_Sesion 
            SET estado = 'Cerrado', fecha_fin = %s 
            WHERE id_chat = %s
        """, (datetime.now(), id_chat))
        
        conn.commit()
        
        return JSONResponse({"success": True, "message": "Chat cerrado con éxito"})
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Cerrar Chat): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
