from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import decimal # Para manejar el dinero de forma segura
import random # Para simular la referencia

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])

# ==========================================================
#  RUTAS DE DEPÓSITO Y GUARDADO DE CLABE (Ya existentes)
# ==========================================================

@router.post("/deposit-card")
async def api_deposit_card(
    id_usuario: int = Form(), 
    monto: str = Form(),
    numero_tarjeta: str = Form(),
    nombre_titular: str = Form(),
    fecha_exp: str = Form(),
    cvv: str = Form()
):
    print(f"🔹 API: Procesando depósito de ${monto} con tarjeta para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        # 1. Registrar la transacción como 'Completada'
        cursor.execute(
            "INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago) VALUES (%s, 'Depósito', %s, 'Completada', 'Tarjeta')",
            (id_usuario, monto_decimal)
        )
        # 2. Actualizar el saldo del usuario
        cursor.execute(
            "UPDATE Saldo SET saldo_actual = saldo_actual + %s WHERE id_usuario = %s",
            (monto_decimal, id_usuario)
        )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Depósito realizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Deposit Card): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


@router.post("/save-method-bank")
async def api_save_bank_method(
    id_usuario: int = Form(),
    clabe: str = Form(),
    nombre_banco: str = Form()
):
    print(f"🔹 API: Guardando CLABE para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id_metodo FROM Metodo_Pago WHERE nombre = 'Transferencia'")
        metodo = cursor.fetchone()
        if not metodo:
            return JSONResponse({"error": "Configuración del servidor incompleta (M-406)"}, status_code=500)
        id_metodo_pago = metodo['id_metodo']

        # Guardamos la CLABE como token
        # Verificamos si ya existe
        cursor.execute(
            "SELECT id_metodo_usuario FROM Usuario_Metodo_Pago WHERE id_usuario = %s AND id_metodo = %s",
            (id_usuario, id_metodo_pago)
        )
        existing = cursor.fetchone()

        if existing:
            # Update
            cursor.execute(
                "UPDATE Usuario_Metodo_Pago SET token_externo = %s WHERE id_metodo_usuario = %s",
                (clabe, existing['id_metodo_usuario'])
            )
        else:
            # Insert
            cursor.execute(
                "INSERT INTO Usuario_Metodo_Pago (id_usuario, id_metodo, token_externo) VALUES (%s, %s, %s)",
                (id_usuario, id_metodo_pago, clabe)
            )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Método de pago (CLABE) guardado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Save CLABE): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  RUTAS DE RETIRO (Ya existentes)
# ==========================================================
@router.post("/withdraw-bank")
async def api_withdraw_bank(
    id_usuario: int = Form(),
    monto: str = Form(),
    clabe: str = Form()
):
    print(f"🔹 API: Solicitando retiro de ${monto} a CLABE {clabe} para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Verificar saldo suficiente
        cursor.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (id_usuario,))
        saldo = cursor.fetchone()
        
        if not saldo or saldo['saldo_actual'] < monto_decimal:
            return JSONResponse({"error": "Saldo insuficiente."}, status_code=400)

        # 2. Descontar saldo
        cursor.execute(
            "UPDATE Saldo SET saldo_actual = saldo_actual - %s, ultima_actualizacion = %s WHERE id_usuario = %s",
            (monto_decimal, datetime.now(), id_usuario)
        )

        # 3. Registrar transacción (Pendiente)
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES (%s, 'Retiro', %s, 'Pendiente', 'Transferencia', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )

        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Retiro solicitado correctamente."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Withdraw Bank): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/withdraw-card")
async def api_withdraw_card(
    id_usuario: int = Form(),
    monto: str = Form(),
    numero_tarjeta: str = Form()
):
    print(f"🔹 API: Solicitando retiro de ${monto} a Tarjeta {numero_tarjeta} para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Verificar saldo suficiente
        cursor.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (id_usuario,))
        saldo = cursor.fetchone()
        
        if not saldo or saldo['saldo_actual'] < monto_decimal:
            return JSONResponse({"error": "Saldo insuficiente."}, status_code=400)

        # 2. Descontar saldo
        cursor.execute(
            "UPDATE Saldo SET saldo_actual = saldo_actual - %s, ultima_actualizacion = %s WHERE id_usuario = %s",
            (monto_decimal, datetime.now(), id_usuario)
        )

        # 3. Registrar transacción (Pendiente)
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES (%s, 'Retiro', %s, 'Pendiente', 'Tarjeta', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )

        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Retiro solicitado correctamente."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Withdraw Card): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  NUEVO: GUARDAR MÉTODO DE PAGO (TARJETA)
# ==========================================================
@router.post("/save-method-card")
async def api_save_card_method(
    id_usuario: int = Form(),
    numero_tarjeta: str = Form(),
    nombre_titular: str = Form(),
    fecha_exp: str = Form()
    # No pedimos el CVV, NUNCA se debe guardar
):
    """
    Guarda (simula) una tarjeta de crédito/débito en la tabla
    Usuario_Metodo_Pago.
    Llamada por: account-tarjeta.html
    """
    print(f"🔹 API: Guardando Tarjeta para usuario: {id_usuario}")
    
    # Validación simple
    if len(numero_tarjeta) < 15 or len(numero_tarjeta) > 16:
        return JSONResponse({"error": "Número de tarjeta inválido."}, status_code=400)
    if len(fecha_exp) < 5: # (MM/AA)
        return JSONResponse({"error": "Fecha de expiración inválida."}, status_code=400)

    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Averiguamos el id_metodo para 'Tarjeta'
        # Asumiré que en tu tabla 'Metodo_Pago' tienes uno llamado 'Tarjeta'
        cursor.execute("SELECT id_metodo FROM Metodo_Pago WHERE nombre = 'Tarjeta'")
        metodo = cursor.fetchone()
        
        if not metodo:
            print("🚨 API ERROR: No se encontró 'Tarjeta' en la tabla Metodo_Pago")
            return JSONResponse({"error": "Configuración del servidor incompleta (M-405)"}, status_code=500)

        id_metodo_pago = metodo['id_metodo']

        # 2. SIMULACIÓN DE TOKEN: NUNCA guardes la tarjeta real.
        # Guardamos solo los últimos 4 dígitos como "token".
        token_simulado = f"XXXX-XXXX-XXXX-{numero_tarjeta[-4:]}"

        # 3. Usamos 'UPSERT' (UPDATE o INSERT)
        # 3. Manual UPSERT
        cursor.execute(
            "SELECT id_metodo_usuario FROM Usuario_Metodo_Pago WHERE id_usuario = %s AND id_metodo = %s",
            (id_usuario, id_metodo_pago)
        )
        existing = cursor.fetchone()

        if existing:
            # Update
            cursor.execute(
                """
                UPDATE Usuario_Metodo_Pago 
                SET token_externo = %s, fecha_registro = %s 
                WHERE id_metodo_usuario = %s
                """,
                (token_simulado, datetime.now(), existing['id_metodo_usuario'])
            )
        else:
            # Insert
            cursor.execute(
                """
                INSERT INTO Usuario_Metodo_Pago (id_usuario, id_metodo, token_externo, fecha_registro)
                VALUES (%s, %s, %s, %s)
                """,
                (id_usuario, id_metodo_pago, token_simulado, datetime.now())
            )
        
        conn.commit()
        
        print(f"✅ API: Tarjeta guardada para {id_usuario}")
        return JSONResponse({"success": True, "message": "Método de pago (tarjeta) guardado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Guardar Tarjeta): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  NUEVO: DEPÓSITO POR TRANSFERENCIA (GENERAR REFERENCIA)
# ==========================================================
@router.post("/deposit-transfer")
async def api_deposit_transfer(
    id_usuario: int = Form(),
    monto: str = Form()
):
    """
    Crea una transacción 'Pendiente' para un depósito por transferencia.
    Llamada por: account-cartera-deposito-transferencia.html
    """
    print(f"🔹 API: Generando referencia de depósito de ${monto} para usuario: {id_usuario}")

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
        # ¡¡IMPORTANTE!! El estado es 'Pendiente'
        cursor.execute(
            """
            INSERT INTO Transaccion 
                (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES 
                (%s, 'Depósito', %s, 'Pendiente', 'Transferencia', %s)
            RETURNING id_transaccion
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        # Obtenemos el ID de la transacción que acabamos de crear
        id_transaccion = cursor.fetchone()[0]
        
        # PASO 2: Simular un número de referencia (normalmente lo daría un banco)
        # Usamos el ID + un número aleatorio para que sea único
        referencia_simulada = f"RC-{id_transaccion}{random.randint(1000, 9999)}"

        # PASO 3: Confirmar la transacción
        conn.commit()
        
        print(f"✅ API: Referencia {referencia_simulada} generada para {id_usuario}")
        return JSONResponse({
            "success": True, 
            "message": "Referencia generada con éxito.",
            "referencia": referencia_simulada,
            "monto": float(monto_decimal)
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Depósito Transfer): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
