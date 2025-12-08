from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import decimal

router = APIRouter(tags=["Blackjack"])

# ========== CONSTANTES DEL JUEGO ==========

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

# ========== MODELOS ==========

class BetRequest(BaseModel):
    amount: int

# ========== ALMACENAMIENTO EN MEMORIA PARA ESTADO DEL JUEGO ==========
# Nota: En producción con múltiples workers, considera usar Redis
game_states = {}

# ========== FUNCIONES DEL JUEGO ==========

def new_deck():
    deck = [(r, s) for s in SUITS for r in RANKS] * 4
    random.shuffle(deck)
    return deck

def card_value(rank):
    if rank == "A":
        return 11
    if rank in ("J","Q","K"):
        return 10
    return int(rank)

def hand_value(hand):
    total = 0
    aces = 0
    for r, s in hand:
        total += card_value(r)
        if r == "A":
            aces += 1
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21

def get_game_state(user_id: int):
    """Obtiene el estado del juego del usuario o crea uno nuevo"""
    conn = None
    try:
        conn = db_connect.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (user_id,))
        saldo_obj = cur.fetchone()
        current_bank = float(saldo_obj['saldo_actual']) if saldo_obj else 500
        cur.close()
    except Exception as e:
        print(f"Error obteniendo saldo: {e}")
        current_bank = 500
    finally:
        if conn: conn.close()
    
    if user_id not in game_states:
        # Crear nuevo estado de juego
        game_states[user_id] = {
            "deck": new_deck(),
            "player": [],
            "dealer": [],
            "bet": 0,
            "bank": current_bank,
            "phase": "BETTING",  # BETTING, PLAYER, DEALER, END
            "message": "HAZ TU APUESTA",
        }
    else:
        # Actualizar bank con el valor de la BD (sincronizar)
        game_states[user_id]["bank"] = current_bank
    
    return game_states[user_id]

def save_game_state(user_id: int, g: dict):
    """Guarda el estado del juego y sincroniza con PostgreSQL"""
    game_states[user_id] = g
    # Sincronizar saldo con PostgreSQL
    conn = None
    try:
        conn = db_connect.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Saldo SET saldo_actual = %s, ultima_actualizacion = NOW() WHERE id_usuario = %s",
            (decimal.Decimal(str(g["bank"])), user_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error guardando saldo: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn: conn.close()

def draw_card(g, who):
    if not g["deck"]:
        g["deck"] = new_deck()
    card = g["deck"].pop()
    g[who].append(card)

def allowed_actions(g):
    phase = g["phase"]
    actions = []
    if phase == "BETTING":
        actions = ["bet", "clear_bet", "deal"]
    elif phase == "PLAYER":
        actions = ["hit", "stand"]
        if len(g["player"]) == 2 and g["bet"] * 2 <= g["bank"]:
            actions.append("double")
    elif phase == "END":
        actions = ["new_round"]
    return actions

def serialize_state(g):
    return {
        "player": g["player"],
        "dealer": g["dealer"],
        "player_value": hand_value(g["player"]) if g["player"] else 0,
        "dealer_value": hand_value(g["dealer"]) if g["dealer"] else 0,
        "bet": g["bet"],
        "bank": g["bank"],
        "phase": g["phase"],
        "message": g["message"],
        "allowed_actions": allowed_actions(g),
        "dealer_hidden": g["phase"] == "PLAYER" and len(g["dealer"]) >= 2
    }

def resolve_blackjack(g):
    p = is_blackjack(g["player"])
    d = is_blackjack(g["dealer"])
    if p and d:
        g["message"] = "EMPATE"
    elif p:
        win = int(g["bet"] * 1.5)
        g["bank"] += win
        g["message"] = f"¡BLACKJACK! +${win}"
    else:
        g["bank"] -= g["bet"]
        g["message"] = "BLACKJACK DEL DEALER"
    g["phase"] = "END"

# ========== HELPER PARA OBTENER USER_ID DE COOKIES ==========

def get_user_id_from_cookie(request: Request):
    """Obtiene el user_id desde la cookie userId"""
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        return int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Cookie inválida")

# ========== ENDPOINTS DEL JUEGO BLACKJACK ==========

@router.get("/api/state")
async def api_state(request: Request):
    """Obtener estado actual del juego"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/bet")
async def api_bet(bet_req: BetRequest, request: Request):
    """Hacer una apuesta"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] != "BETTING":
        return serialize_state(g)
    
    amount = bet_req.amount
    if amount > 0 and g["bet"] + amount <= g["bank"]:
        g["bet"] += amount
        g["message"] = f"APUESTA: ${g['bet']}"
    else:
        g["message"] = "FONDOS INSUFICIENTES"
    
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/clear_bet")
async def api_clear_bet(request: Request):
    """Borrar apuesta"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] == "BETTING":
        g["bet"] = 0
        g["message"] = "APUESTA BORRADA"
    
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/deal")
async def api_deal(request: Request):
    """Repartir cartas"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] != "BETTING":
        return serialize_state(g)
    
    if g["bet"] <= 0:
        g["message"] = "HAZ UNA APUESTA"
        save_game_state(user_id, g)
        return serialize_state(g)
    
    if g["bet"] > g["bank"]:
        g["message"] = "FONDOS INSUFICIENTES"
        save_game_state(user_id, g)
        return serialize_state(g)

    # Limpiar manos
    g["player"] = []
    g["dealer"] = []

    # Repartir
    draw_card(g, "player")
    draw_card(g, "dealer")
    draw_card(g, "player")
    draw_card(g, "dealer")

    g["phase"] = "PLAYER"
    g["message"] = ""

    # Verificar blackjack
    if is_blackjack(g["player"]) or is_blackjack(g["dealer"]):
        resolve_blackjack(g)

    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/hit")
async def api_hit(request: Request):
    """Pedir carta"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] != "PLAYER":
        return serialize_state(g)
    
    draw_card(g, "player")
    if hand_value(g["player"]) > 21:
        g["bank"] -= g["bet"]
        g["message"] = "TE PASASTE"
        g["phase"] = "END"
    
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/stand")
async def api_stand(request: Request):
    """Mantenerse"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] != "PLAYER":
        return serialize_state(g)
    
    # Turno dealer
    while hand_value(g["dealer"]) < 17:
        draw_card(g, "dealer")
    
    pv = hand_value(g["player"])
    dv = hand_value(g["dealer"])
    
    if dv > 21:
        g["bank"] += g["bet"]
        g["message"] = "DEALER SE PASÓ • GANASTE"
    elif pv > dv:
        g["bank"] += g["bet"]
        g["message"] = "GANASTE"
    elif pv < dv:
        g["bank"] -= g["bet"]
        g["message"] = "PERDISTE"
    else:
        g["message"] = "EMPATE"
    
    g["phase"] = "END"
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/double")
async def api_double(request: Request):
    """Doblar apuesta"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    if g["phase"] != "PLAYER":
        return serialize_state(g)
    
    if len(g["player"]) != 2 or g["bet"] * 2 > g["bank"]:
        return serialize_state(g)

    g["bank"] -= g["bet"]
    g["bet"] *= 2
    draw_card(g, "player")
    
    if hand_value(g["player"]) > 21:
        g["message"] = "TE PASASTE"
        g["phase"] = "END"
    else:
        # Doble = 1 carta y stand automático
        while hand_value(g["dealer"]) < 17:
            draw_card(g, "dealer")
        
        pv = hand_value(g["player"])
        dv = hand_value(g["dealer"])
        
        if dv > 21 or pv > dv:
            g["bank"] += g["bet"]
            g["message"] = "GANASTE"
        elif pv < dv:
            g["message"] = "PERDISTE"
        else:
            g["message"] = "EMPATE"
        
        g["phase"] = "END"
    
    save_game_state(user_id, g)
    return serialize_state(g)

@router.post("/api/new_round")
async def api_new_round(request: Request):
    """Nueva ronda"""
    user_id = get_user_id_from_cookie(request)
    g = get_game_state(user_id)
    
    g["player"] = []
    g["dealer"] = []
    g["bet"] = 0
    g["phase"] = "BETTING"
    g["message"] = "HAZ TU APUESTA"
    
    save_game_state(user_id, g)
    return serialize_state(g)
