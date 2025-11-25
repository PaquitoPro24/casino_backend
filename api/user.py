from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

@router.get("/api/user/{id_usuario}")
async def api_get_user_info(id_usuario: int):
    """
    Ruta para OBTENER la info del usuario y rellenar el formulario
    Llamada por: account-configuracion.html y account-cartera-historial.html
    """
    print(f"🔹 API: Pidiendo info para usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtenemos todos los datos que el formulario necesita
        cursor.execute(
            """
            SELECT
                u.nombre,
                u.apellido,
                u.email,
                u.rol,
                s.saldo_actual
            FROM
                Usuario u
            LEFT JOIN
                Saldo s ON u.id_usuario = s.id_usuario
            WHERE
                u.id_usuario = %s AND u.activo = true
            """, 
            (id_usuario,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return JSONResponse({"error": "Usuario no encontrado o inactivo"}, status_code=404)
        
        # Convertimos Decimal a float para que JSONResponse funcione
        return JSONResponse({
            "nombre": usuario['nombre'],
            "apellido": usuario['apellido'],
            "email": usuario['email'],
            "saldo": float(usuario['saldo_actual'] or 0.0), # (Añadido 'or 0.0' por si es None)
            "rol": usuario['rol']
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (get_user_info): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  RUTA PARA ACTUALIZAR EL PERFIL (GUARDAR CAMBIOS)
# ==========================================================
@router.put("/api/user/update/{id_usuario}")
async def api_update_user_info(
    id_usuario: int,
    nombre: str = Form(),
    apellido: str = Form(),
    email: str = Form()
):
    """
    Ruta para GUARDAR los cambios del formulario de 'account-configuracion.html'
    """
    print(f"🔹 API: Actualizando perfil para: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 1. Ejecutar el UPDATE en la tabla 'Usuario'
        cursor.execute(
            """
            UPDATE Usuario
            SET nombre = %s, apellido = %s, email = %s
            WHERE id_usuario = %s
            """,
            (nombre, apellido, email, id_usuario)
        )
        
        # 2. Confirmar la transacción
        conn.commit()
        
        cursor.close()
        
        print(f"✅ API: Perfil actualizado para {id_usuario}")
        return JSONResponse({"success": True, "message": "Perfil actualizado exitosamente"})

    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        print(f"❌ API: Conflicto, email ya existe")
        return JSONResponse({"error": "Ese correo electrónico ya está en uso por otra cuenta."}, status_code=409)
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (update_user_info): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if conn: conn.close()
