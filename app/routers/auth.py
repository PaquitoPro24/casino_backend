from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

# Importamos la función para conectar a la BD
from app.db.db_connect import get_connection

# 1. Modelo Pydantic: Define la estructura de datos que esperamos recibir.
# FastAPI usará esto para validar que el JSON del frontend es correcto.
# Los nombres de los campos (correo, contrasena) deben coincidir con el JavaScript.
class UserLogin(BaseModel):
    correo: EmailStr
    contrasena: str


# Creamos un "router" para organizar las rutas de autenticación
router = APIRouter(
    prefix="/api/auth",  # Todas las rutas aquí empezarán con /api/auth
    tags=["Authentication"]
)


@router.post("/login")
def login(user_credentials: UserLogin):
    """
    Endpoint para manejar el inicio de sesión.
    Recibe credenciales en formato JSON y las valida contra la base de datos.
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error de conexión con la base de datos."
            )

        with conn.cursor() as cur:
            # ❗ IMPORTANTE: Asumimos que tu tabla se llama 'usuarios' y tiene estas columnas.
            # Si los nombres son diferentes, ajústalos aquí.
            cur.execute(
                "SELECT id_usuario, contrasena, rol FROM usuarios WHERE correo = %s",
                (user_credentials.correo,)
            )
            db_user = cur.fetchone()

            # Si el correo no existe en la base de datos
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correo o contraseña incorrectos."
                )

            db_id_usuario, db_contrasena, db_rol = db_user

            # ⚠️ ADVERTENCIA DE SEGURIDAD:
            # Esta es una comparación de texto plano, lo cual es MUY INSEGURO.
            # Deberías usar una librería como 'passlib' para hashear contraseñas.
            # Por ahora, para que funcione, lo dejamos así.
            if user_credentials.contrasena != db_contrasena:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Correo o contraseña incorrectos."
                )

            # Si todo es correcto, devolvemos los datos que el frontend espera
            return JSONResponse(content={
                "id_usuario": db_id_usuario,
                "rol": db_rol
            })

    except Exception as e:
        # Capturamos cualquier error para devolver una respuesta controlada
        print(f"❌ Error en el endpoint de login: {e}")
        # Si es una excepción HTTP que ya definimos, la relanzamos
        if isinstance(e, HTTPException):
            raise e
        # Para cualquier otro error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {e}"
        )
    finally:
        if conn:
            conn.close()