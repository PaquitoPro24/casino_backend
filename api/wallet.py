from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import decimal # Para manejar el dinero de forma segura

router = APIRouter()

@router.post("/api/wallet/deposit-card")
async def api_deposit_card(
    # Tu HTML aún no lo pide, pero lo necesitaremos
    # id_usuario: int = Form(), 
    
    # Por ahora, simularemos con el usuario 1
    # Cuando tu <script> envíe el ID, quita esta línea:
    id_usuario: int = 1, 
    
    # Tu formulario HTML (account-cartera-deposito-tarjeta.html)
    # no tiene 'name' en los inputs. Asumiré que el monto
    # se llama 'monto'.
    monto: str = Form() 
):
    """
    Ruta para procesar un DEPÓSITO con tarjeta.
    Esto debe ser una TRANSACCIÓN DE BASE DE DATOS.
    """
    print(f"🔹 API: Intento de depósito de ${monto} para usuario: {id_usuario}")
    
    # Validar y convertir el monto
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)
    except Exception:
        return JSONResponse({"error": "Monto inválido."}, status_code=400)
        
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        # ¡IMPORTANTE! Iniciamos una transacción.
        # O ambos comandos (INSERT y UPDATE) funcionan, o ninguno lo hace.
        cursor = conn.cursor()

        # PASO 1: Registrar la transacción en la tabla 'Transaccion'
        cursor.execute(
            """
            INSERT INTO Transaccion 
                (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES 
                (%s, 'Depósito', %s, 'Completada', 'Tarjeta', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        # PASO 2: Actualizar el saldo del usuario en la tabla 'Saldo'
        cursor.execute(
            """
            UPDATE Saldo
            SET saldo_actual = saldo_actual + %s,
                ultima_actualizacion = %s
            WHERE id_usuario = %s
            """,
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        # Si ambos comandos funcionaron, confirmamos los cambios
        conn.commit()
        
        print(f"✅ API: Depósito exitoso para {id_usuario}")
        return JSONResponse({"success": True, "message": "Depósito realizado con éxito."})

    except Exception as e:
        # Si algo falló, revertimos TODOS los cambios
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Depósito): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
