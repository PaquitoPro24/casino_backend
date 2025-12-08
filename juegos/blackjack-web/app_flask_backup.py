# app.py PARA APP INVENTOR
from flask import Flask, session, jsonify, send_from_directory, request, make_response
import random
import os
from db_config import get_user_balance, update_user_balance

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-dev-key")

# Configuración de sesión para App Inventor
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Requiere HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

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

# -------------------- STATE HELPERS -------------------- #

def get_game():
    """Obtiene el estado actual desde la sesión o crea uno nuevo."""
    g = session.get("game")
    user_id = session.get("user_id")
    
    if not g:
        # Cargar saldo inicial desde PostgreSQL si hay user_id
        initial_bank = 500
        if user_id:
            initial_bank = get_user_balance(user_id)
        
        g = {
            "deck": new_deck(),
            "player": [],
            "dealer": [],
            "bet": 0,
            "bank": initial_bank,
            "phase": "BETTING",  # BETTING, PLAYER, DEALER, END
            "message": "HAZ TU APUESTA",
        }
    
    # Recarga automática si está en bancarrota
    if g["bank"] < 5 and g["bet"] == 0:
        g["bank"] = 500
        g["message"] = "¡BANCARROTA! TE REGALAMOS $500"
        # Actualizar en PostgreSQL
        if user_id:
            update_user_balance(user_id, g["bank"])
        
    return g

def save_game(g):
    session["game"] = g
    # Sincronizar saldo con PostgreSQL si hay user_id
    user_id = session.get("user_id")
    if user_id:
        update_user_balance(user_id, g["bank"])

def draw_card(g, who):
    if not g["deck"]:
        g["deck"] = new_deck()
    card = g["deck"].pop()
    g[who].append(card)

def set_message(g, msg):
    g["message"] = msg

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

# -------------------- API -------------------- #

@app.route("/api/login", methods=["GET"])
def api_login():
    """
    Endpoint para iniciar sesión desde App Inventor.
    Recibe user_id como query param y establece la sesión.
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400
    
    # Limpiar sesión anterior
    session.clear()
    session.permanent = True
    
    # Guardar user_id en sesión
    session["user_id"] = user_id
    
    # Inicializar juego y cargar saldo desde PostgreSQL
    g = get_game()
    save_game(g)
    
    # Crear respuesta con cookie de sesión explícita
    response = make_response(jsonify({
        "status": "success",
        "user_id": user_id,
        "saldo": g["bank"],
        "message": "Sesión iniciada correctamente"
    }))
    
    return response

@app.route("/")
def index():
    # Obtener user_id de query params
    user_id = request.args.get('user_id')
    
    # Reiniciar juego al cargar la página
    session.clear()
    
    # Guardar user_id en sesión si existe
    if user_id:
        session["user_id"] = user_id
    
    return send_from_directory("static", "index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    g = get_game()
    save_game(g)
    return jsonify(serialize_state(g))

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
        # ocultamos la segunda carta del dealer mientras está en fase PLAYER
        "dealer_hidden": g["phase"] == "PLAYER" and len(g["dealer"]) >= 2
    }

@app.route("/api/bet", methods=["POST"])
def api_bet():
    g = get_game()
    if g["phase"] != "BETTING":
        return jsonify(serialize_state(g))
    data = request.get_json(force=True)
    amount = int(data.get("amount", 0))
    if amount > 0 and g["bet"] + amount <= g["bank"]:
        g["bet"] += amount
        set_message(g, f"APUESTA: ${g['bet']}")
    else:
        set_message(g, "FONDOS INSUFICIENTES")
    save_game(g)
    return jsonify(serialize_state(g))

@app.route("/api/clear_bet", methods=["POST"])
def api_clear_bet():
    g = get_game()
    if g["phase"] == "BETTING":
        g["bet"] = 0
        set_message(g, "APUESTA BORRADA")
    save_game(g)
    return jsonify(serialize_state(g))

@app.route("/api/deal", methods=["POST"])
def api_deal():
    g = get_game()
    if g["phase"] != "BETTING":
        return jsonify(serialize_state(g))
    if g["bet"] <= 0:
        set_message(g, "HAZ UNA APUESTA")
        save_game(g)
        return jsonify(serialize_state(g))
    if g["bet"] > g["bank"]:
        set_message(g, "FONDOS INSUFICIENTES")
        save_game(g)
        return jsonify(serialize_state(g))

    # limpiar manos
    g["player"] = []
    g["dealer"] = []

    # repartir
    draw_card(g, "player")
    draw_card(g, "dealer")
    draw_card(g, "player")
    draw_card(g, "dealer")

    g["phase"] = "PLAYER"
    set_message(g, "")

    # verificar blackjack
    if is_blackjack(g["player"]) or is_blackjack(g["dealer"]):
        resolve_blackjack(g)

    save_game(g)
    return jsonify(serialize_state(g))

def resolve_blackjack(g):
    p = is_blackjack(g["player"])
    d = is_blackjack(g["dealer"])
    if p and d:
        set_message(g, "EMPATE")
    elif p:
        win = int(g["bet"] * 1.5)
        g["bank"] += win
        set_message(g, f"¡BLACKJACK! +${win}")
    else:
        g["bank"] -= g["bet"]
        set_message(g, "BLACKJACK DEL DEALER")
    g["phase"] = "END"

@app.route("/api/hit", methods=["POST"])
def api_hit():
    g = get_game()
    if g["phase"] != "PLAYER":
        return jsonify(serialize_state(g))
    draw_card(g, "player")
    if hand_value(g["player"]) > 21:
        g["bank"] -= g["bet"]
        set_message(g, "TE PASASTE")
        g["phase"] = "END"
    save_game(g)
    return jsonify(serialize_state(g))

@app.route("/api/stand", methods=["POST"])
def api_stand():
    g = get_game()
    if g["phase"] != "PLAYER":
        return jsonify(serialize_state(g))
    # turno dealer
    while hand_value(g["dealer"]) < 17:
        draw_card(g, "dealer")
    pv = hand_value(g["player"])
    dv = hand_value(g["dealer"])
    if dv > 21:
        g["bank"] += g["bet"]
        set_message(g, "DEALER SE PASÓ • GANASTE")
    elif pv > dv:
        g["bank"] += g["bet"]
        set_message(g, "GANASTE")
    elif pv < dv:
        g["bank"] -= g["bet"]
        set_message(g, "PERDISTE")
    else:
        set_message(g, "EMPATE")
    g["phase"] = "END"
    save_game(g)
    return jsonify(serialize_state(g))

@app.route("/api/double", methods=["POST"])
def api_double():
    g = get_game()
    if g["phase"] != "PLAYER":
        return jsonify(serialize_state(g))
    if len(g["player"]) != 2 or g["bet"] * 2 > g["bank"]:
        return jsonify(serialize_state(g))

    g["bank"] -= g["bet"]
    g["bet"] *= 2
    draw_card(g, "player")
    if hand_value(g["player"]) > 21:
        set_message(g, "TE PASASTE")
        g["phase"] = "END"
    else:
        # como en casino: doble = 1 carta y stand automático
        while hand_value(g["dealer"]) < 17:
            draw_card(g, "dealer")
        pv = hand_value(g["player"])
        dv = hand_value(g["dealer"])
        if dv > 21 or pv > dv:
            g["bank"] += g["bet"]
            set_message(g, "GANASTE")
        elif pv < dv:
            set_message(g, "PERDISTE")
        else:
            set_message(g, "EMPATE")
        g["phase"] = "END"
    save_game(g)
    return jsonify(serialize_state(g))

@app.route("/api/new_round", methods=["POST"])
def api_new_round():
    g = get_game()
    g["player"] = []
    g["dealer"] = []
    g["bet"] = 0
    g["phase"] = "BETTING"
    set_message(g, "HAZ TU APUESTA")
    save_game(g)
    return jsonify(serialize_state(g))

# ----------------- DEV HELPER ----------------- #
if __name__ == "__main__":
    app.run(debug=True)
