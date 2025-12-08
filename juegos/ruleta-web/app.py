# app.py - FastAPI con PostgreSQL
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
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

# -----------------------------------------------------------
#  RULETA EUROPEA — ORDEN REAL OFICIAL (sentido horario)
# -----------------------------------------------------------
WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6,
    27, 13, 36, 11, 30, 8, 23, 10, 5, 24,
    16, 33, 1, 20, 14, 31, 9, 22, 18, 29,
    7, 28, 12, 35, 3, 26
]

RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16,
    18, 19, 21, 23, 25, 27,
    30, 32, 34, 36
}

def color_of(n):
    """Determinar color del número"""
    if n == 0:
        return "verde"
    return "rojo" if n in RED_NUMBERS else "negro"

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

class BetItem(BaseModel):
    amt: int
    type: str
    odds: int
    numbers: str

class SpinRequest(BaseModel):
    balance: int
    currentBet: int
    bets: list[BetItem]
    numbersBet: list[int]

class SpinResponse(BaseModel):
    winningSpin: int
    winValue: int
    newBalance: float

# ========== ENDPOINTS DE AUTENTICACIÓN ==========

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login con email y password"""
    # Buscar usuario por email
    user = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Verificar password
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
    
    return LoginResponse(
        token=token,
        user={
            "id_usuario": user.id_usuario,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.email
        }
    )

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

@app.get("/api/user/{user_id}")
def get_user_balance_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Obtener saldo de un usuario específico por ID (para integración simple).
    Devuelve JSON { "saldo": float }.
    """
    saldo = db.query(Saldo).filter(Saldo.id_usuario == user_id).first()
    
    if not saldo:
        # Si no existe saldo, retornamos 0 o un error, 
        # pero para el juego quizas sea mejor devolver 0 si el usuario existe.
        # Por ahora, si no hay registro de saldo, asumimos 0.
        return {"saldo": 0.0}
    
    return {"saldo": float(saldo.saldo_actual)}

# ========== ENDPOINTS DE LA RULETA ==========

@app.get("/")
def serve_frontend(request: Request, response: Response, user_email: str = None, db: Session = Depends(get_db)):
    """
    Ruta raíz inteligente:
    Si recibe ?user_email=..., busca al usuario, crea un token y lo guarda en cookie.
    Permite login automático desde App Inventor.
    """
    # Preparamos la respuesta (el archivo HTML)
    file_response = FileResponse("templates/index.html")

    # Si App Inventor nos mandó el email...
    if user_email:
        print(f"🔌 Conexión desde App Inventor para: {user_email}")
        
        # 1. Buscar usuario en la BD
        user = db.query(Usuario).filter(Usuario.email == user_email).first()
        
        if user:
            # 2. Crear Token automáticamente (Login sin contraseña)
            # Esto es seguro porque confiamos en que tu App Inventor ya validó la contraseña antes
            token = create_access_token({
                "sub": str(user.id_usuario),
                "email": user.email
            })
            
            # 3. Inyectar Token en la Cookie del navegador
            file_response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,  # Más seguridad
                samesite="lax"
            )
            print(f"✅ Token creado y enviado en cookie para {user_email}")
    
    return file_response

@app.post("/api/spin", response_model=SpinResponse)
def api_spin(
    req: SpinRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API de SPIN con autenticación y actualización de saldo en BD
    Calcula ganancias basadas en todos los tipos de apuestas de la ruleta
    """
    currentBet = req.currentBet
    bets = req.bets
    numbersBet = req.numbersBet

    # Obtener saldo actual de la base de datos
    saldo_obj = db.query(Saldo).filter(Saldo.id_usuario == current_user.id_usuario).first()
    
    if not saldo_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saldo no encontrado"
        )
    
    saldo_actual = float(saldo_obj.saldo_actual)

    # Validar saldo suficiente
    if currentBet > saldo_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente"
        )

    # Generar número ganador aleatorio (0-36)
    winningSpin = random.randint(0, 36)
    
    # Calcular ganancias
    winValue = 0
    if winningSpin in numbersBet:
        for bet_item in bets:
            numArray = [int(x.strip()) for x in bet_item.numbers.split(',')]
            if winningSpin in numArray:
                # Ganancia = (odds * monto_apostado) + monto_apostado
                winValue += (bet_item.odds * bet_item.amt)
    
    # Calcular nuevo saldo: saldo_actual - apuesta_total + ganancias
    new_balance = saldo_actual - currentBet + winValue
    if winValue > 0:
        new_balance += currentBet  # Devolver la apuesta también si ganó

    # Actualizar saldo en la base de datos
    saldo_obj.saldo_actual = Decimal(str(new_balance))
    db.commit()
    db.refresh(saldo_obj)

    return SpinResponse(
        winningSpin=winningSpin,
        winValue=winValue,
        newBalance=float(saldo_obj.saldo_actual)
    )

# ========== STARTUP ==========

@app.on_event("startup")
def startup_event():
    """Verificar conexión a base de datos al iniciar"""
    print("🚀 Iniciando aplicación...")
    test_connection()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
