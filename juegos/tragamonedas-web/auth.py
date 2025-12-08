import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
# CAMBIO 1: Usar Argon2 para ser compatible con tu App de Registro
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario

# Usamos Argon2 (igual que en tu otro proyecto)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "tu-secret-key-super-segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False) # No lanzar error automático para permitir cookies

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# CAMBIO 2: Función inteligente que busca el token en Header O en Cookie
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Usuario:
    
    token = None
    
    # 1. Intentar leer del Header (Authorization: Bearer ...)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 2. Si no hay header, intentar leer de la COOKIE (Para App Inventor)
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user_id = payload.get("sub") # Aquí guardamos el ID
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token sin ID")
    
    # Buscar usuario en BD
    user = db.query(Usuario).filter(Usuario.id_usuario == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
    return user