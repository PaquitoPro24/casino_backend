from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Rol(Base):
    __tablename__ = 'rol'
    
    id_rol = Column(Integer, primary_key=True)
    nombre = Column(String(30), unique=True, nullable=False)
    descripcion = Column(Text)

class Usuario(Base):
    __tablename__ = 'usuario'
    
    id_usuario = Column(Integer, primary_key=True)
    id_rol = Column(Integer, ForeignKey('rol.id_rol'), nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    curp = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    saldo = relationship("Saldo", uselist=False, back_populates="usuario")

class Saldo(Base):
    __tablename__ = 'saldo'
    
    id_saldo = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    saldo_actual = Column(Numeric(10, 2), nullable=False, default=0)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="saldo")
