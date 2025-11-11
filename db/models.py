"""
Modelos SQLAlchemy (placeholder).
Cuando integremos la BD real, definimos aquí:

- Usuario, Rol
- Juego, Partida
- MetodoPago, Transaccion
- Bono, UsuarioBono
- CasoSoporte, MensajeSoporte

Ejemplo de esqueleto:
---------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship
from .database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    id_usuario = Column(Integer, primary_key=True, index=True)
    correo = Column(String(255), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    nombre = Column(String(120))
    apellidos = Column(String(180))
    estado_cuenta = Column(String(20), default="Activo")
"""
