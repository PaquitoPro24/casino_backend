from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
# ... existing code ...
# ==========================================================
#  OBTENER LISTA DE ADMINS (Para 'admin-administradores.html')
# ==========================================================
@router.get("/api/admin/administradores")
# ... existing code ...
    finally:
        if conn: conn.close()

# ==========================================================
#  GESTIÓN DE PERFIL DE USUARIO (Para 'admin-usuario-perfil.html')
# ==========================================================

@router.get("/api/admin/user-profile/{id_usuario}")
async def api_get_user_profile(id_usuario: int):
    """
    Obtiene los datos completos de un usuario para rellenar el formulario de admin.
    """
    print(f"🔹 API Admin: Pidiendo perfil de usuario: {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Unimos Usuario y Saldo para tener toda la info
        cursor.execute(
            """
            SELECT 
                u.id_usuario, u.nombre, u.apellido, u.curp, u.email, u.rol, u.activo,
                s.saldo_actual
            FROM Usuario u
            LEFT JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.id_usuario = %s
            """,
            (id_usuario,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)
        
        # Convertimos Decimal a float para que JSONResponse no falle
        usuario['saldo_actual'] = float(usuario['saldo_actual'] or 0.0)
        
        return JSONResponse(usuario)

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Profile): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


@router.put("/api/admin/user-profile/{id_usuario}")
async def api_update_user_profile(
    id_usuario: int,
    nombre: str = Form(),
    apellido: str = Form(),
    email: str = Form(),
    curp: str = Form(),
    rol: str = Form(),
    activo: str = Form() # Vendrá como "true" o "false" (string)
):
    """
    Actualiza los datos de un usuario desde el panel de admin.
    """
    print(f"🔹 API Admin: Actualizando perfil de usuario: {id_usuario}")
    conn = None
    cursor = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # Convertimos el 'activo' de string a boolean
        activo_bool = (activo.lower() == 'true')
        
        # Actualizamos la tabla Usuario
        cursor.execute(
            """
            UPDATE Usuario
            SET 
                nombre = %s,
                apellido = %s,
                email = %s,
                curp = %s,
                rol = %s,
                activo = %s
            WHERE id_usuario = %s
            """,
            (nombre, apellido, email, curp, rol, activo_bool, id_usuario)
        )
        
        conn.commit()
        
        print(f"✅ API Admin: Perfil actualizado para {id_usuario}")
        return JSONResponse({"success": True, "message": "Perfil actualizado con éxito."})

    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        return JSONResponse({"error": "El email o la CURP ya están en uso por otra cuenta."}, status_code=409)
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Admin Update Profile): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
