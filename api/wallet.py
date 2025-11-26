from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import decimal # Para manejar el dinero de forma segura
import random # Para simular la referencia

router = APIRouter()

# ==========================================================
#  RUTAS DE DEPÓSITO Y GUARDADO DE CLABE (Ya existentes)
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
    print(f"🔹 API: Procesando depósito de ${monto} con tarjeta para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        # Validaciones básicas de tarjeta
        if len(numero_tarjeta) < 15 or len(numero_tarjeta) > 16:
            return JSONResponse({"error": "Número de tarjeta inválido."}, status_code=400)
        if len(fecha_exp) < 5:
            return JSONResponse({"error": "Fecha de expiración inválida."}, status_code=400)
        if len(cvv) < 3 or len(cvv) > 4:
            return JSONResponse({"error": "CVV inválido."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        # 1. Registrar la transacción como 'Completada'
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES (%s, 'Depósito', %s, 'Completada', 'Tarjeta', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        # 2. Actualizar el saldo del usuario
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
        cursor.close()
        return JSONResponse({"success": True, "message": "Depósito realizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Deposit Card): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


@router.post("/api/wallet/save-method-bank")
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
            # Si no existe, lo creamos automáticamente
            cursor.execute(
                "INSERT INTO Metodo_Pago (nombre, tipo, activo) VALUES ('Transferencia', 'Transferencia', true) RETURNING id_metodo"
            )
            id_metodo_pago = cursor.fetchone()['id_metodo']
        else:
            id_metodo_pago = metodo['id_metodo']

        # Guardamos la CLABE como token
        cursor.execute(
            """
            INSERT INTO Usuario_Metodo_Pago (id_usuario, id_metodo, token_externo) VALUES (%s, %s, %s)
            ON CONFLICT (id_usuario, id_metodo) DO UPDATE SET token_externo = EXCLUDED.token_externo
            """,
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
@router.post("/api/wallet/withdraw-bank")
async def api_withdraw_bank(
    id_usuario: int = Form(),
    monto: str = Form()
):
    """
    Procesa un retiro a cuenta bancaria, verifica saldo y actualiza la base de datos
    """
    print(f"🔹 API: Solicitando retiro de ${monto} a CLABE para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 1. Verificar saldo suficiente
        cursor.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()
        
        if not result:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)
        
        saldo_actual = result[0]
        if saldo_actual < monto_decimal:
            return JSONResponse({"error": "Saldo insuficiente"}, status_code=400)
        
        # 2. Registrar la transacción como 'Completada'
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES (%s, 'Retiro', %s, 'Completada', 'Transferencia', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        # 3. Actualizar el saldo del usuario
        cursor.execute(
            """
            UPDATE Saldo 
            SET saldo_actual = saldo_actual - %s,
                ultima_actualizacion = %s
            WHERE id_usuario = %s
            """,
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        conn.commit()
        cursor.close()
        
        print(f"✅ API: Retiro a banco completado para usuario {id_usuario}")
        return JSONResponse({"success": True, "message": "Retiro realizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Withdraw Bank): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/api/wallet/withdraw-card")
async def api_withdraw_card(
    id_usuario: int = Form(),
    monto: str = Form()
):
    """
    Procesa un retiro a tarjeta, verifica saldo y actualiza la base de datos
    """
    print(f"🔹 API: Solicitando retiro de ${monto} a Tarjeta para usuario: {id_usuario}")
    conn = None
    try:
        monto_decimal = decimal.Decimal(monto)
        if monto_decimal <= 0:
            return JSONResponse({"error": "El monto debe ser positivo."}, status_code=400)

        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 1. Verificar saldo suficiente
        cursor.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (id_usuario,))
        result = cursor.fetchone()
        
        if not result:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)
        
        saldo_actual = result[0]
        if saldo_actual < monto_decimal:
            return JSONResponse({"error": "Saldo insuficiente"}, status_code=400)
        
        # 2. Registrar la transacción como 'Completada'
        cursor.execute(
            """
            INSERT INTO Transaccion (id_usuario, tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion)
            VALUES (%s, 'Retiro', %s, 'Completada', 'Tarjeta', %s)
            """,
            (id_usuario, monto_decimal, datetime.now())
        )
        
        # 3. Actualizar el saldo del usuario
        cursor.execute(
            """
            UPDATE Saldo 
            SET saldo_actual = saldo_actual - %s,
                ultima_actualizacion = %s
            WHERE id_usuario = %s
            """,
            (monto_decimal, datetime.now(), id_usuario)
        )
        
        conn.commit()
        cursor.close()
        
        print(f"✅ API: Retiro completado para usuario {id_usuario}")
        return JSONResponse({"success": True, "message": "Retiro realizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Withdraw Card): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  NUEVO: GUARDAR MÉTODO DE PAGO (TARJETA)
# ==========================================================
@router.post("/api/wallet/save-method-card")
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
        cursor.execute("SELECT id_metodo FROM Metodo_Pago WHERE nombre = 'Tarjeta'")
        metodo = cursor.fetchone()
        
        if not metodo:
            # Si no existe, lo creamos automáticamente
            cursor.execute(
                "INSERT INTO Metodo_Pago (nombre, tipo, activo) VALUES ('Tarjeta', 'Tarjeta', true) RETURNING id_metodo"
            )
            id_metodo_pago = cursor.fetchone()['id_metodo']
        else:
            id_metodo_pago = metodo['id_metodo']

        # 2. SIMULACIÓN DE TOKEN: NUNCA guardes la tarjeta real.
        # Guardamos solo los últimos 4 dígitos como "token".
        token_simulado = f"XXXX-XXXX-XXXX-{numero_tarjeta[-4:]}"

        # 3. Usamos 'UPSERT' (UPDATE o INSERT)
        cursor.execute(
            """
            INSERT INTO Usuario_Metodo_Pago (id_usuario, id_metodo, token_externo, fecha_registro)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id_usuario, id_metodo) -- Si ya tiene una tarjeta registrada
            DO UPDATE SET token_externo = EXCLUDED.token_externo,
                          fecha_registro = EXCLUDED.fecha_registro
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
@router.post("/api/wallet/deposit-transfer")
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

# ==========================================================
#  NUEVO: HISTORIAL DE TRANSACCIONES
# ==========================================================
@router.get("/api/wallet/transactions/{id_usuario}")
async def api_get_transactions(id_usuario: int):
    """
    Obtiene el historial de transacciones (depósitos y retiros) del usuario.
    """
    print(f"🔹 API: Obteniendo transacciones para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT tipo_transaccion, monto, estado, metodo_pago, fecha_transaccion
            FROM Transaccion
            WHERE id_usuario = %s
            ORDER BY fecha_transaccion DESC
            """,
            (id_usuario,)
        )
        transacciones = cursor.fetchall()
        cursor.close()
        
        # Convertir datetime a ISO format para JSON
        for tx in transacciones:
            if tx.get('fecha_transaccion'):
                tx['fecha_transaccion'] = tx['fecha_transaccion'].isoformat()
            if tx.get('monto'):
                tx['monto'] = float(tx['monto'])
        
        return JSONResponse({"transacciones": transacciones})

    except Exception as e:
        print(f"🚨 API ERROR (Get Transactions): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  NUEVO: HISTORIAL DE JUEGOS
# ==========================================================
@router.get("/api/wallet/game-history/{id_usuario}")
async def api_get_game_history(id_usuario: int):
    """
    Obtiene el historial de juegos del usuario.
    NOTA: Por ahora devuelve una lista vacía o datos simulados si no existe la tabla.
    """
    print(f"🔹 API: Obteniendo historial de juegos para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Intentamos consultar una tabla hipotética 'Historial_Juego'
        # Si falla, devolvemos lista vacía para no romper el frontend
        try:
            cursor.execute(
                """
                SELECT h.id_historial, j.nombre as nombre_juego, h.fecha_inicio, h.fecha_fin, h.ganancia
                FROM Historial_Juego h
                JOIN Juego j ON h.id_juego = j.id_juego
                WHERE h.id_usuario = %s
                ORDER BY h.fecha_inicio DESC
                """,
                (id_usuario,)
            )
            games = cursor.fetchall()
        except psycopg2.Error:
            if conn: conn.rollback()
            print("⚠️ API: Tabla Historial_Juego no encontrada, devolviendo lista vacía.")
            games = []

        cursor.close()
        
        return JSONResponse({"games": games})

    except Exception as e:
        print(f"🚨 API ERROR (Get Game History): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
