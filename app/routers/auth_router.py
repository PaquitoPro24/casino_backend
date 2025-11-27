from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

# Importamos la función para conectar a la BD
from app.db.db_connect import get_connection

# 1. Modelo Pydantic: Define la estructura de datos que esperamos recibir.
# FastAPI usará esto para validar que el JSON del frontend es correcto.
class UserLogin(BaseModel):
    correo: EmailStr
    contrasena: str


# Creamos un "router" para organizar las rutas de autenticación
router = APIRouter(
    # El prefijo ya se define en main.py, así que aquí no es estrictamente necesario,
    # pero es buena práctica para la organización.
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

        # Usamos un cursor que devuelve diccionarios para acceder a las columnas por nombre
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT id_usuario, contrasena, rol FROM usuarios WHERE correo = %s",
                (user_credentials.correo,)
            )
            user = cur.fetchone()

            # Si el correo no existe o la contraseña no coincide
            if not user or user["contrasena"] != user_credentials.contrasena:
                # ⚠️ ADVERTENCIA DE SEGURIDAD:
                # La comparación de contraseñas en texto plano es INSEGURA.
                # Se debe usar una librería como 'passlib' para hashear contraseñas.
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Correo o contraseña incorrectos."
                )

            # ✅ Si todo es correcto, devolvemos los datos que el frontend espera
            return JSONResponse(content={
                "id_usuario": user["id_usuario"],
                "rol": user["rol"]
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