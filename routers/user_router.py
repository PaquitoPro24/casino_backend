from fastapi import APIRouter
from app.db.db_connect import get_connection

router = APIRouter()

@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario, nombre_usuario, correo, saldo, estado_cuenta FROM usuarios WHERE id_usuario=%s", (id_usuario,))
    data = cursor.fetchone()
    conn.close()
    return data
