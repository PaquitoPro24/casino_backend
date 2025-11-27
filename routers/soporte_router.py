from fastapi import APIRouter, Form
from app.db.db_connect import get_connection

router = APIRouter()

@router.post("/crear_ticket")
def crear_ticket(id_usuario: int = Form(...), asunto: str = Form(...), descripcion: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (id_usuario_recibe, asunto, descripcion) VALUES (%s, %s, %s)",
                   (id_usuario, asunto, descripcion))
    conn.commit()
    conn.close()
    return {"message": "📨 Ticket creado correctamente"}

@router.get("/listar_tickets/{id_usuario}")
def listar_tickets(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tickets WHERE id_usuario_recibe=%s", (id_usuario,))
    tickets = cursor.fetchall()
    conn.close()
    return tickets
