"""
Conexión a base de datos (placeholder).
Cuando integremos BD, aquí va el engine y SessionLocal.

Ejemplo MySQL (cuando te pases a BD real):
------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+pymysql://usuario:password@localhost/royal_crumbs?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
"""

# Placeholders para que los imports no fallen
SessionLocal = None
Base = object
engine = None
