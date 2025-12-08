from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional
import random
import os

# Importar módulos de base de datos y autenticación
from database import get_db, test_connection
from models import Usuario, Saldo
from auth import verify_password, create_access_token, get_current_user

app = FastAPI()

# PERMITIR CUALQUIER ORIGEN (web + app inventor)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SERVIR CARPETA STATIC
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== CONSTANTES DEL JUEGO ==========

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

# ========== MODELOS DE PYDANTIC ==========

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

class SaldoResponse(BaseModel):
    saldo: float
    usuario: dict

class BetRequest(BaseModel):
    amount: int

class GameState(BaseModel):
    player: list
    dealer: list
    player_value: int
    dealer_value: int
    bet: int
    bank: int
    phase: str
    message: str
    allowed_actions: list
    dealer_hidden: bool

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

def get_game_state(user_id: int, db: Session):
    """Obtiene el estado del juego del usuario o crea uno nuevo"""
    # Siempre obtener saldo actualizado desde PostgreSQL
    saldo_obj = db.query(Saldo).filter(Saldo.id_usuario == user_id).first()
    current_bank = float(saldo_obj.saldo_actual) if saldo_obj else 500
    
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

def save_game_state(user_id: int, g: dict, db: Session):
    """Guarda el estado del juego y sincroniza con PostgreSQL"""
    game_states[user_id] = g
    # Sincronizar saldo con PostgreSQL
    saldo_obj = db.query(Saldo).filter(Saldo.id_usuario == user_id).first()
    if saldo_obj:
        saldo_obj.saldo_actual = Decimal(str(g["bank"]))
        db.commit()

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

# ========== ENDPOINTS DE AUTENTICACIÓN ==========

    response = LoginResponse(
        token=token,
        user={
            "id_usuario": user.id_usuario,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.email
        }
    )
    
    # Inyectar Token en la Cookie del navegador (para acceso web directo)
    # Usamos Response de FastAPI que se puede inyectar en el endpoint si se declara,
    # pero como estamos retornando un modelo Pydantic, necesitamos usar un truco o cambiar la firma.
    # Mejor opción: Usar Response como parámetro y setear cookie.
    return response

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login con email y password"""
    user = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Crear token JWT
    token = create_access_token({
        "sub": str(user.id_usuario),
        "email": user.email
    })
    
    # Setear cookie para persistencia en web
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 días
    )
    
    return LoginResponse(
        token=token,
        user={
            "id_usuario": user.id_usuario,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.email
        }
    )

# ========== ENDPOINT RAÍZ CON LOGIN AUTOMÁTICO ==========

@app.get("/")
def serve_frontend(request: Request, response: Response, user_email: str = None, db: Session = Depends(get_db)):
    """
    Ruta raíz inteligente:
    Si recibe ?user_email=..., busca al usuario, crea un token y lo guarda en cookie.
    Permite login automático desde App Inventor.
    """
    file_response = FileResponse("static/index.html")

    # 1. Caso App Inventor: ?user_email=...
    if user_email:
        print(f"🔌 Conexión desde App Inventor para: {user_email}")
        user = db.query(Usuario).filter(Usuario.email == user_email).first()
        
        if user:
            token = create_access_token({
                "sub": str(user.id_usuario),
                "email": user.email
            })
            file_response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="lax"
            )
            print(f"✅ Token creado y enviado en cookie para {user_email}")
        return file_response

    # 2. Caso Web Directo: Verificar si ya tiene cookie válida
    token = request.cookies.get("access_token")
    if token:
        # Aquí podríamos validar el token, pero si es inválido, 
        # las llamadas a API fallarán (401) y el frontend redirigirá a login.
        # Para ser más robustos, podemos intentar decodificarlo rápido.
        from auth import decode_token
        if decode_token(token):
            return file_response

    # 3. Si no hay auth, servir index.html de todas formas
    # El frontend manejará el estado "no autenticado" (ej. sin saldo, sin juego)
    # o esperará a que el usuario entre con ?user_email=...
    return file_response

# ========== ENDPOINTS DE SALDO ==========

@app.get("/api/saldo", response_model=SaldoResponse)
def get_saldo(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener saldo actual del usuario autenticado"""
    saldo = db.query(Saldo).filter(Saldo.id_usuario == current_user.id_usuario).first()
    
    if not saldo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saldo no encontrado"
        )
    
    return SaldoResponse(
        saldo=float(saldo.saldo_actual),
        usuario={
            "nombre": current_user.nombre,
            "apellido": current_user.apellido
        }
    )

# ========== ENDPOINTS DEL JUEGO BLACKJACK ==========

@app.get("/api/state", response_model=GameState)
def api_state(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener estado actual del juego"""
    g = get_game_state(current_user.id_usuario, db)
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/bet", response_model=GameState)
def api_bet(bet_req: BetRequest, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hacer una apuesta"""
    g = get_game_state(current_user.id_usuario, db)
    
    if g["phase"] != "BETTING":
        return serialize_state(g)
    
    amount = bet_req.amount
    if amount > 0 and g["bet"] + amount <= g["bank"]:
        g["bet"] += amount
        g["message"] = f"APUESTA: ${g['bet']}"
    else:
        g["message"] = "FONDOS INSUFICIENTES"
    
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/clear_bet", response_model=GameState)
def api_clear_bet(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Borrar apuesta"""
    g = get_game_state(current_user.id_usuario, db)
    
    if g["phase"] == "BETTING":
        g["bet"] = 0
        g["message"] = "APUESTA BORRADA"
    
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/deal", response_model=GameState)
def api_deal(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Repartir cartas"""
    g = get_game_state(current_user.id_usuario, db)
    
    if g["phase"] != "BETTING":
        return serialize_state(g)
    
    if g["bet"] <= 0:
        g["message"] = "HAZ UNA APUESTA"
        save_game_state(current_user.id_usuario, g, db)
        return serialize_state(g)
    
    if g["bet"] > g["bank"]:
        g["message"] = "FONDOS INSUFICIENTES"
        save_game_state(current_user.id_usuario, g, db)
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

    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/hit", response_model=GameState)
def api_hit(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pedir carta"""
    g = get_game_state(current_user.id_usuario, db)
    
    if g["phase"] != "PLAYER":
        return serialize_state(g)
    
    draw_card(g, "player")
    if hand_value(g["player"]) > 21:
        g["bank"] -= g["bet"]
        g["message"] = "TE PASASTE"
        g["phase"] = "END"
    
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/stand", response_model=GameState)
def api_stand(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mantenerse"""
    g = get_game_state(current_user.id_usuario, db)
    
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
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/double", response_model=GameState)
def api_double(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Doblar apuesta"""
    g = get_game_state(current_user.id_usuario, db)
    
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
    
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

@app.post("/api/new_round", response_model=GameState)
def api_new_round(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Nueva ronda"""
    g = get_game_state(current_user.id_usuario, db)
    
    g["player"] = []
    g["dealer"] = []
    g["bet"] = 0
    g["phase"] = "BETTING"
    g["message"] = "HAZ TU APUESTA"
    
    save_game_state(current_user.id_usuario, g, db)
    return serialize_state(g)

# ========== STARTUP ==========

@app.on_event("startup")
def startup_event():
    """Verificar conexión a base de datos al iniciar"""
    print("🚀 Iniciando aplicación Blackjack...")
    test_connection()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
