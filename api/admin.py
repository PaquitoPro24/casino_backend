from fastapi import APIRouter
from fastapi.responses import JSONResponse
import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

# ==========================================================
#  OBTENER ESTADÍSTICAS (Para 'admin-info-general.html')
# ==========================================================
@router.get("/api/admin/stats")
async def api_get_admin_stats():
    """
    Obtiene las estadísticas principales para el dashboard del admin.
    """
    print(f"🔹 API: Pidiendo estadísticas de administrador")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Contar usuarios totales
        cursor.execute("SELECT COUNT(id_usuario) AS total_usuarios FROM Usuario")
        total_usuarios = cursor.fetchone()['total_usuarios']
        
        # 2. Contar usuarios activos
        cursor.execute("SELECT COUNT(id_usuario) AS usuarios_activos FROM Usuario WHERE activo = true")
        usuarios_activos = cursor.fetchone()['usuarios_activos']
        
        # 3. Sumar todos los depósitos
        cursor.execute("""
            SELECT SUM(monto) AS total_depositos 
            FROM Transaccion 
            WHERE tipo_transaccion = 'Depósito' AND estado = 'Completada'
        """)
        total_depositos = cursor.fetchone()['total_depositos'] or 0.0
        
        # 4. Sumar todos los retiros
        cursor.execute("""
            SELECT SUM(monto) AS total_retiros 
            FROM Transaccion 
            WHERE tipo_transaccion = 'Retiro' AND estado = 'Completada'
        """)
        total_retiros = cursor.fetchone()['total_retiros'] or 0.0

        cursor.close()
        
        return JSONResponse({
            "total_usuarios": total_usuarios,
            "usuarios_activos": usuarios_activos,
            "total_depositos": float(total_depositos),
            "total_retiros": float(total_retiros)
        })

    except Exception as e:
        print(f"🚨 API ERROR (Admin Stats): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  OBTENER LISTA DE USUARIOS (Para 'admin-usuarios.html')
# ==========================================================
@router.get("/api/admin/usuarios")
async def api_get_all_users():
    """
    Obtiene la lista de todos los usuarios con rol 'Jugador'.
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT id_usuario, nombre, apellido, email, activo
            FROM Usuario
            WHERE rol = 'Jugador'
            ORDER BY fecha_registro DESC
            """
        )
        usuarios = cursor.fetchall()
        cursor.close()
        return JSONResponse({"usuarios": usuarios})

    except Exception as e:
        print(f"🚨 API ERROR (Listar Usuarios): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
        
# ==========================================================
#  OBTENER LISTA DE ADMINS (Para 'admin-administradores.html')
# ==========================================================
@router.get("/api/admin/administradores")
async def api_get_all_admins():
    """
    Obtiene la lista de todos los usuarios con rol 'Administrador' o 'Auditor'.
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT id_usuario, nombre, apellido, email, rol, activo
            FROM Usuario
            WHERE rol IN ('Administrador', 'Auditor')
            ORDER BY rol
            """
        )
        admins = cursor.fetchall()
        cursor.close()
        return JSONResponse({"admins": admins})

    except Exception as e:
        print(f"🚨 API ERROR (Listar Admins): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
