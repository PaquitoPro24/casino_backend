from fastapi import APIRouter
from app.db.db_connect import get_connection

router = APIRouter()

@router.get("/disponibles/{id_usuario}")
def bonos_usuario(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.nombre_bono, b.descripcion, ub.estado 
        FROM usuario_bono ub
        JOIN bonos b ON b.id_bono = ub.id_bono
        WHERE ub.id_usuario = %s
    """, (id_usuario,))
    data = cursor.fetchall()
    conn.close()
    return data
