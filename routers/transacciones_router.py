from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import decimal

router = APIRouter()

@router.post("/api/transacciones/depositar")
async def depositar(
    id_usuario: int = Form(),
    monto: str = Form(),
    metodo: str = Form()
):
    """
    Procesa un depósito y actualiza el saldo del usuario
    """
    print(f"🔹 API: Depósito de ${monto} para usuario {id_usuario}")
    conn = None
    cursor = None
    
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo"}, status_code=400)
        
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Insertar transacción con nombres correctos de columnas
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, metodo_pago, monto, estado, fecha_transaccion)
            VALUES (%s, 'Depósito', %s, %s, 'Completada', %s)
            """,
            (id_usuario, metodo, monto_decimal, datetime.now())
        )
        
        # Actualizar saldo en la tabla Saldo (no usuarios)
        cursor.execute(
            "UPDATE Saldo SET saldo_actual = saldo_actual + %s, ultima_actualizacion = %s WHERE id_usuario = %s",
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        conn.commit()
        
        print(f"✅ Depósito completado para usuario {id_usuario}")
        return JSONResponse({"success": True, "message": "Depósito realizado correctamente"})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🚨 API ERROR (Depositar): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/api/transacciones/retirar")
async def retirar(
    id_usuario: int = Form(),
    monto: str = Form()
):
    """
    Procesa un retiro verificando saldo suficiente
    """
    print(f"🔹 API: Retiro de ${monto} para usuario {id_usuario}")
    conn = None
    cursor = None
    
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo"}, status_code=400)
        
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar saldo disponible
        cursor.execute(
            "SELECT saldo_actual FROM Saldo WHERE id_usuario = %s",
            (id_usuario,)
        )
        saldo_info = cursor.fetchone()
        
        if not saldo_info or saldo_info['saldo_actual'] < monto_decimal:
            return JSONResponse({"error": "Saldo insuficiente"}, status_code=400)
        
        # Actualizar saldo
        cursor.execute(
            "UPDATE Saldo SET saldo_actual = saldo_actual - %s, ultima_actualizacion = %s WHERE id_usuario = %s",
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        # Registrar transacción de retiro
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, fecha_transaccion)
            VALUES (%s, 'Retiro', %s, 'Completada', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ Retiro completado para usuario {id_usuario}")
        return JSONResponse({"success": True, "message": "Retiro realizado correctamente"})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"🚨 API ERROR (Retirar): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/api/transacciones/historial/{id_usuario}")
async def historial(id_usuario: int):
    """
    Obtiene el historial de transacciones de un usuario
    """
    print(f"🔹 API: Historial de transacciones para usuario {id_usuario}")
    conn = None
    
    try:
        conn = get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener transacciones con nombres correctos
        cursor.execute(
            """
            SELECT 
                id_transaccion,
                tipo_transaccion,
                monto,
                estado,
                metodo_pago,
                fecha_transaccion
            FROM Transaccion
            WHERE id_usuario = %s
            ORDER BY fecha_transaccion DESC
            LIMIT 100
            """,
            (id_usuario,)
        )
        
        transacciones = cursor.fetchall()
        cursor.close()
        
        # Convertir decimales a float para JSON
        for t in transacciones:
            if t['monto']:
                t['monto'] = float(t['monto'])
        
        return JSONResponse({"transacciones": transacciones})
        
    except Exception as e:
        print(f"🚨 API ERROR (Historial): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn:
            conn.close()
