from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import db_connect
import random
import decimal

router = APIRouter(prefix="/api", tags=["Games"])

# Modelos
class SpinRequest(BaseModel):
    bet: int

class ReelRequest(BaseModel):
    reel_index: int

# Constantes del juego (Tragamonedas)
SYMBOLS = ["❔", "🍒", "🍋", "🍇", "⭐", "7️⃣", "🔔"]
PAYOUTS = {
    "🍒": 2,    # x2
    "🍋": 3,    # x3
    "🍇": 5,    # x5
    "⭐": 10,   # x10
    "7️⃣": 20,   # x20
    "🔔": 50    # x50
}

@router.post("/reel")
async def api_get_reel(request: ReelRequest):
    """
    Genera símbolos aleatorios para un rodillo.
    Se llama 3 veces (una por rodillo) desde el frontend.
    """
    # Lógica simple: retornar 3 símbolos aleatorios
    symbols = [random.choice(SYMBOLS) for _ in range(3)]
    return {"symbols": symbols}

@router.post("/spin")
async def api_spin(request: Request, spin_data: SpinRequest):
    """
    Procesa la apuesta, descuenta saldo y calcula ganancias.
    """
    user_id = request.cookies.get("userId")
    if not user_id:
         # Intentar leer de query param si no hay cookie (para iframes cross-origin si fuera el caso, pero aquí es mismo origen)
         # Pero por seguridad, confiemos en la cookie o el frontend debe pasar el ID.
         # El frontend usa credentials: 'include', así que la cookie debería llegar.
         return JSONResponse({"detail": "No autenticado. Por favor inicie sesión."}, status_code=401)

    bet = spin_data.bet
    if bet <= 0:
        return JSONResponse({"detail": "La apuesta debe ser mayor a 0"}, status_code=400)

    conn = None
    try:
        conn = db_connect.get_connection()
        cwd = conn.cursor()

        # 1. Verificar saldo
        cwd.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (user_id,))
        res = cwd.fetchone()
        if not res:
            return JSONResponse({"detail": "Usuario no encontrado"}, status_code=404)
        
        saldo_actual = float(res[0])
        if saldo_actual < bet:
            return JSONResponse({"detail": "Saldo insuficiente"}, status_code=400)

        # 2. Descontar apuesta
        nueva_saldo = saldo_actual - bet
        cwd.execute("UPDATE Saldo SET saldo_actual = %s WHERE id_usuario = %s", (nueva_saldo, user_id))
        
        # 3. Calcular Victoria (RNG Simple por ahora para integración)
        # Probabilidad de ganar: 30%
        win_amount = 0
        is_win = random.random() < 0.3
        
        if is_win:
            # Multiplicador aleatorio simple (x2 a x5)
            multiplier = random.choice([2, 3, 5]) 
            win_amount = bet * multiplier
            
            # Actualizar saldo con ganancia
            nueva_saldo += win_amount
            cwd.execute("UPDATE Saldo SET saldo_actual = %s WHERE id_usuario = %s", (nueva_saldo, user_id))

        # 4. Registrar Transacción (Opcional, pero bueno para historial)
        # Solo registramos si hay cambio significativo o si se desea log de juego
        # Por rendimiento, a veces los spins no se loguean en transacciones bancarias, 
        # pero aquí es un casino simple.
        
        conn.commit()
        cwd.close()

        return {
            "win": win_amount,
            "nuevo_saldo": nueva_saldo,
            "detail": "Jiro completado"
        }

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Spin): {e}")
        return JSONResponse({"detail": "Error interno del servidor"}, status_code=500)
    finally:
        if conn: conn.close()

# Roulette-specific models
class RouletteSpinRequest(BaseModel):
    balance: float
    currentBet: float
    bets: list
    numbersBet: list

@router.post("/spin-roulette")
async def api_spin_roulette(request: Request, spin_data: RouletteSpinRequest):
    """
    Procesa el giro de ruleta y calcula ganancias basadas en las apuestas.
    """
    user_id = request.cookies.get("userId")
    if not user_id:
        return JSONResponse({"detail": "No autenticado"}, status_code=401)

    conn = None
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()

        # Generar número ganador (0-36)
        winning_spin = random.randint(0, 36)
        
        # Calcular ganancias basadas en las apuestas
        win_value = 0
        for bet in spin_data.bets:
            bet_numbers = [int(x.strip()) for x in bet['numbers'].split(',')]
            if winning_spin in bet_numbers:
                win_value += bet['amt'] * bet['odds']
        
        # Actualizar saldo en BD
        new_balance = spin_data.balance + win_value
        cursor.execute("UPDATE Saldo SET saldo_actual = %s WHERE id_usuario = %s", (new_balance, user_id))
        conn.commit()
        cursor.close()

        return {
            "winningSpin": winning_spin,
            "winValue": win_value,
            "newBalance": new_balance
        }

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Roulette Spin): {e}")
        return JSONResponse({"detail": "Error interno del servidor"}, status_code=500)
    finally:
        if conn: conn.close()

