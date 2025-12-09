from fastapi import APIRouter, Form, Request # <-- ¡AQUÍ ESTÁ LA CORRECCIÓN!
from fastapi.responses import JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/api/user", tags=["User"])

@router.get("/{id_usuario}")
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
                r.nombre as rol,
                s.saldo_actual
            FROM
                Usuario u
            JOIN
                Rol r ON u.id_rol = r.id_rol
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
@router.put("/update/{id_usuario}")
async def api_update_user_info(
    id_usuario: int,
    nombre: str = Form(),
    apellido: str = Form(),
    email: str = Form(),
    contrasena: str = Form(None) # Opcional
):
    """
    Ruta para GUARDAR los cambios del formulario de 'account-configuracion.html'
    Ahora soporta cambio de contraseña.
    """
    print(f"🔹 API: Actualizando perfil para: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 1. Update básico (Nombre, Apellido, Email)
        cursor.execute(
            """
            UPDATE Usuario
            SET nombre = %s, apellido = %s, email = %s
            WHERE id_usuario = %s
            """,
            (nombre, apellido, email, id_usuario)
        )
        
        # 2. Si hay contraseña nueva, actualizarla también
        if contrasena and contrasena.strip():
            print(f"🔹 API: Actualizando contraseña para usuario {id_usuario}")
            from api.auth import pwd_context # Importar aquí para evitar circular import si fuera necesario, o usar el global si está movido.
            # Mejor importar pwd_context de un lugar comun si es posible, o re-instanciar.
            # Dado que auth.py lo instancia, podemos importarlo de ahí. 
            # api.auth ya está importado en main, así que debería estar bien.
            
            hashed_password = pwd_context.hash(contrasena)
            
            cursor.execute(
                """
                UPDATE Usuario
                SET password_hash = %s
                WHERE id_usuario = %s
                """,
                (hashed_password, id_usuario)
            )

        # 3. Confirmar la transacción
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


