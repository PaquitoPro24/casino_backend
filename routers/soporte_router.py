from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime

router = APIRouter()

@router.post("/crear_ticket")
async def crear_ticket(
    id_usuario: int = Form(...),
    asunto: str = Form(...),
    descripcion: str = Form(...)
):
    """
    Crea un ticket de soporte
    NOTA: El endpoint principal está en /api/support/tickets/create
    Este es un router alternativo/redundante
    """
    print(f"🔹 Router: Creando ticket para usuario {id_usuario}")
    conn = None
    cursor = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Insertar en tabla Soporte con nombres correctos de columnas
        cursor.execute(
            """
            INSERT INTO Soporte (id_jugador, asunto, mensaje, estado, fecha_creacion)
            VALUES (%s, %s, %s, 'Abierto', %s)
            """,
            (id_usuario, asunto, descripcion, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ Ticket creado para usuario {id_usuario}")
        return JSONResponse({"success": True, "message": "Ticket creado correctamente"})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🚨 Error al crear ticket: {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/listar_tickets/{id_usuario}")
async def listar_tickets(id_usuario: int):
    """
    Lista los tickets de un usuario
    NOTA: El endpoint principal está en /api/support/tickets/active/{id_usuario}
    Este es un router alternativo/redundante
    """
    print(f"🔹 Router: Listando tickets del usuario {id_usuario}")
    conn = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consultar tabla Soporte con nombres correctos
        cursor.execute(
            """
            SELECT id_ticket, asunto, mensaje, estado, fecha_creacion
            FROM Soporte
            WHERE id_jugador = %s
            ORDER BY fecha_creacion DESC
            """,
            (id_usuario,)
        )
        
        tickets = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"tickets": tickets})
        
    except Exception as e:
        print(f"🚨 Error al listar tickets: {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
