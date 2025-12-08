import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Leer DATABASE_URL de variables de entorno (Render la proporciona automáticamente)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en las variables de entorno")

# Fix para Render: cambiar postgres:// a postgresql://
# SQLAlchemy moderno requiere postgresql:// en lugar de postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear engine de SQLAlchemy con pool de conexiones
engine = create_engine(
    DATABASE_URL,
    pool_size=5,              # Número de conexiones permanentes
    max_overflow=10,          # Conexiones adicionales en picos
    pool_pre_ping=True        # Verificar conexiones antes de usar
)

# Session maker para crear sesiones de BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()

# Dependency para FastAPI - Inyección de dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para probar conexión al iniciar
def test_connection():
    try:
        with engine.connect() as conn:
            print("✅ Conexión exitosa a PostgreSQL")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
