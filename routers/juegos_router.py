from fastapi import APIRouter
from app.db.db_connect import get_connection

router = APIRouter()

@router.get("/listar")
def listar_juegos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM juegos WHERE estado='activo'")
    juegos = cursor.fetchall()
    conn.close()
    return juegos
