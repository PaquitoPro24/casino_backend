from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import decimal # Para manejar el dinero de forma segura

router = APIRouter()

# ==========================================================
#  RUTAS DE DEPÓSITO Y GUARDADO (Ya existentes)
# ==========================================================

@router.post("/api/wallet/deposit-card")
async def api_deposit_card(
    id_usuario: int = Form(), 
    monto: str = Form(),
    numero_tarjeta: str = Form(),
    nombre_titular: str = Form(),
    fecha_exp: str = Form(),
    cvv: str = Form()
):
    """
    Ruta para procesar un DEPÓSITO con tarjeta.
    """
    print(f"🔹 API: Intento de depósito de ${monto} para usuario: {id_usuario}")
    
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
        
        conn.commit()
        
        print(f"✅ API: Depósito exitoso para {id_usuario}")
        return JSONResponse({"success": True, "message": "Depósito realizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Depósito): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@router.post("/api/wallet/save-method-bank")
async def api_save_bank_method(
    id_usuario: int = Form(),
    clabe: str = Form()
):
    """
    Ruta para guardar o actualizar la cuenta CLABE del usuario
    """
    print(f"🔹 API: Guardando CLABE para usuario: {id_usuario}")
    
    if len(clabe) != 18 or not clabe.isdigit():
        return JSONResponse({"error": "La CLABE debe tener 18 dígitos numéricos."}, status_code=400)
        
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Averiguamos el id_metodo para 'Transferencia'
        cursor.execute("SELECT id_metodo FROM Metodo_Pago WHERE nombre = 'Transferencia'")
        metodo = cursor.fetchone()
        
        if not metodo:
            print("🚨 API ERROR: No se encontró 'Transferencia' en la tabla Metodo_Pago")
            return JSONResponse({"error": "Configuración del servidor incompleta (M-404)"}, status_code=500)

        id_metodo_pago = metodo['id_metodo']

        # 2. Usamos 'UPSERT' (UPDATE o INSERT)
        cursor.execute(
            """
            INSERT INTO Usuario_Metodo_Pago (id_usuario, id_metodo, token_externo, fecha_registro)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id_usuario, id_metodo) 
            DO UPDATE SET token_externo = EXCLUDED.token_externo,
                          fecha_registro = EXCLUDED.fecha_registro
            """,
            (id_usuario, id_metodo_pago, clabe, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ API: CLABE guardada para {id_usuario}")
        return JSONResponse({"success": True, "message": "Método de pago guardado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Guardar CLABE): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  NUEVA RUTA: PROCESAR RETIRO (TRANSFERENCIA BANCARIA)
# ==========================================================
@router.post("/api/wallet/withdraw-bank")
async def api_withdraw_bank(
    id_usuario: int = Form(),
    monto: str = Form()
    # 'clabe' se lee de la BD, no del formulario
):
    """
    Procesa un retiro a la CLABE guardada del usuario.
    """
    print(f"🔹 API: Intento de retiro bancario de ${monto} para usuario: {id_usuario}")
    
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
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. VERIFICAR QUE EL USUARIO TENGA UNA CLABE GUARDADA
        cursor.execute(
            """
            SELECT ump.token_externo 
            FROM Usuario_Metodo_Pago ump
            JOIN Metodo_Pago mp ON ump.id_metodo = mp.id_metodo
            WHERE ump.id_usuario = %s AND mp.nombre = 'Transferencia'
            """,
            (id_usuario,)
        )
        metodo_guardado = cursor.fetchone()
        
        if not metodo_guardado or not metodo_guardado['token_externo']:
            return JSONResponse({"error": "No tienes una cuenta CLABE registrada. Por favor, guárdala primero."}, status_code=400)
        
        # 2. VERIFICAR FONDOS (¡Y BLOQUEAR LA FILA!)
        # 'FOR UPDATE' bloquea la fila de Saldo para este usuario,
        # evitando que pueda hacer dos retiros al mismo tiempo (condición de carrera)
        cursor.execute(
            "SELECT saldo_actual FROM Saldo WHERE id_usuario = %s FOR UPDATE",
            (id_usuario,)
        )
        saldo_info = cursor.fetchone()
        
        if not saldo_info or saldo_info['saldo_actual'] < monto_decimal:
            return JSONResponse({"error": "Fondos insuficientes."}, status_code=400)
        
        # 3. SI HAY FONDOS, RESTAR EL SALDO
        cursor.execute(
            """
            UPDATE Saldo
            SET saldo_actual = saldo_actual - %s,
                ultima_actualizacion = %s
            WHERE id_usuario = %s
            """,
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        # 4. REGISTRAR LA TRANSACCIÓN (COMO PENDIENTE)
        # Los retiros suelen ser 'Pendiente' hasta que un admin los aprueba
        cursor.execute(
            """
            INSERT INTO Transaccion 
                (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES 
                (%s, 'Retiro', %s, 'Pendiente', 'Transferencia', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ API: Retiro bancario registrado para {id_usuario}")
        return JSONResponse({"success": True, "message": "Solicitud de retiro enviada. Será procesada en 24-48 horas."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Retiro Banco): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  NUEVA RUTA: PROCESAR RETIRO (TARJETA) - SIMULACIÓN
# ==========================================================
@router.post("/api/wallet/withdraw-card")
async def api_withdraw_card(
    id_usuario: int = Form(),
    monto: str = Form()
):
    """
    Procesa un retiro a tarjeta (Simulación).
    NOTA: En la vida real, necesitaríamos un token de tarjeta guardado.
    """
    print(f"🔹 API: Intento de retiro a tarjeta de ${monto} para usuario: {id_usuario}")
    
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
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. VERIFICAR FONDOS (¡Y BLOQUEAR LA FILA!)
        cursor.execute(
            "SELECT saldo_actual FROM Saldo WHERE id_usuario = %s FOR UPDATE",
            (id_usuario,)
        )
        saldo_info = cursor.fetchone()
        
        if not saldo_info or saldo_info['saldo_actual'] < monto_decimal:
            return JSONResponse({"error": "Fondos insuficientes."}, status_code=400)
        
        # 2. SI HAY FONDOS, RESTAR EL SALDO
        cursor.execute(
            """
            UPDATE Saldo
            SET saldo_actual = saldo_actual - %s,
                ultima_actualizacion = %s
            WHERE id_usuario = %s
            """,
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        # 3. REGISTRAR LA TRANSACCIÓN (COMO PENDIENTE)
        cursor.execute(
            """
            INSERT INTO Transaccion 
                (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES 
                (%s, 'Retiro', %s, 'Pendiente', 'Tarjeta', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        conn.commit()
        
        print(f"✅ API: Retiro a tarjeta registrado para {id_usuario}")
        return JSONResponse({"success": True, "message": "Solicitud de retiro enviada. Será procesada en 24-48 horas."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Retiro Tarjeta): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
