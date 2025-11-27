from fastapi import APIRouter, Form
from app.db.db_connect import get_connection

router = APIRouter()

@router.post("/depositar")
def depositar(id_usuario: int = Form(...), monto: float = Form(...), metodo: str = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transacciones (id_usuario, tipo, metodo, monto, estado) VALUES (%s, 'deposito', %s, %s, 'exitoso')",
                   (id_usuario, metodo, monto))
    cursor.execute("UPDATE usuarios SET saldo = saldo + %s WHERE id_usuario = %s", (monto, id_usuario))
    conn.commit()
    conn.close()
    return {"message": "✅ Depósito realizado correctamente"}

@router.post("/retirar")
def retirar(id_usuario: int = Form(...), monto: float = Form(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id_usuario=%s AND saldo >= %s", (monto, id_usuario, monto))
    cursor.execute("INSERT INTO transacciones (id_usuario, tipo, monto, estado) VALUES (%s, 'retiro', %s, 'exitoso')", (id_usuario, monto))
    conn.commit()
    conn.close()
    return {"message": "💸 Retiro realizado correctamente"}

@router.get("/historial/{id_usuario}")
def historial(id_usuario: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transacciones WHERE id_usuario=%s ORDER BY fecha DESC", (id_usuario,))
    data = cursor.fetchall()
    conn.close()
    return data
