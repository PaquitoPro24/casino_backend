from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect # <-- CORRECCIÓN: Importación relativa
import psycopg2
from psycopg2.extras import RealDictCursor
import decimal # Importamos decimal para manejar dinero
from datetime import datetime # Para manejar fechas

router = APIRouter()

# ==========================================================
#  ESTADÍSTICAS (Ya existente)
# ==========================================================
@router.get("/api/admin/stats")
async def api_get_admin_stats():
    """
    Obtiene estadísticas clave para el dashboard del administrador.
    Llamada por: admin-info-general.html
    """
    print("🔹 API Admin: Pidiendo estadísticas generales")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Total de usuarios (solo jugadores)
        cursor.execute("SELECT COUNT(*) as total_users FROM Usuario WHERE rol = 'Jugador'")
        total_users = cursor.fetchone()['total_users']
        
        # 2. Total de juegos activos
        cursor.execute("SELECT COUNT(*) as active_games FROM Juego WHERE activo = true")
        active_games = cursor.fetchone()['active_games']
        
        # 3. Total de depósitos hoy
        cursor.execute(
            "SELECT COALESCE(SUM(monto), 0) as deposits_today FROM Transaccion WHERE tipo_transaccion = 'Depósito' AND estado = 'Completado' AND fecha_transaccion >= CURRENT_DATE"
        )
        deposits_today = cursor.fetchone()['deposits_today']
        
        cursor.close()
        
        return JSONResponse({
            "total_users": total_users,
            "active_games": active_games,
            "deposits_today": float(deposits_today)
        })

    except Exception as e:
        print(f"🚨 API ERROR (Admin Stats): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  NUEVO: LISTAR USUARIOS Y ADMINS
# ==========================================================
@router.get("/api/admin/usuarios")
async def api_get_all_users():
    """
    Obtiene la lista de todos los usuarios con rol 'Jugador'.
    Llamada por: admin-usuarios.html
    """
    print(f"🔹 API Admin: Pidiendo lista de Jugadores")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscamos solo Jugadores
        cursor.execute(
            "SELECT id_usuario, nombre, apellido, email, activo FROM Usuario WHERE rol = 'Jugador' ORDER BY nombre",
        )
        usuarios = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"users": usuarios})

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Jugadores): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.get("/api/admin/administradores")
async def api_get_all_admins():
    """
    Obtiene la lista de todos los usuarios con rol 'Administrador' o 'Auditor'.
    Llamada por: admin-administradores.html
    """
    print(f"🔹 API Admin: Pidiendo lista de Admins/Auditores")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscamos Admins y Auditores
        cursor.execute(
            "SELECT id_usuario, nombre, apellido, email, rol, activo FROM Usuario WHERE rol IN ('Administrador', 'Auditor') ORDER BY nombre",
        )
        admins = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"admins": admins})

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Admins): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  GESTIÓN DE PERFIL DE USUARIO (Ya existente)
# ==========================================================
@router.get("/api/admin/user-profile/{id_usuario}")
async def api_get_user_profile(id_usuario: int):
    """
    Obtiene el perfil completo de un usuario para el admin.
    Llamada por: admin-usuario-perfil.html
    """
    print(f"🔹 API Admin: Pidiendo perfil de usuario {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, u.rol, u.activo, u.fecha_registro, s.saldo_actual
            FROM Usuario u
            LEFT JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.id_usuario = %s
            """,
            (id_usuario,)
        )
        user_profile = cursor.fetchone()
        cursor.close()

        if not user_profile:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)

        # Aseguramos que el saldo sea un float
        user_profile['saldo_actual'] = float(user_profile['saldo_actual'] or 0.0)
        return JSONResponse(user_profile)

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
    rol: str = Form(),
    activo: bool = Form()
):
    """
    Actualiza el perfil de un usuario desde el panel de admin.
    Llamada por: admin-usuario-perfil.html
    """
    print(f"🔹 API Admin: Actualizando perfil de usuario {id_usuario}")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Usuario SET nombre = %s, apellido = %s, email = %s, rol = %s, activo = %s WHERE id_usuario = %s",
            (nombre, apellido, email, rol, activo, id_usuario)
        )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Perfil actualizado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Admin Update Profile): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  GESTIÓN DE JUEGOS (Ya existente)
# ==========================================================
@router.get("/api/admin/games")
async def api_get_all_games():
    """
    Obtiene la lista de todos los juegos para el admin.
    Llamada por: admin-juegos.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM Juego ORDER BY nombre")
        juegos = cursor.fetchall()
        cursor.close()
        return JSONResponse({"games": juegos})

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Games): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/api/admin/games")
async def api_create_game(
    nombre: str = Form(),
    descripcion: str = Form(),
    rtp: float = Form(),
    min_apuesta: float = Form(),
    max_apuesta: float = Form(),
    activo: bool = Form()
):
    """
    Crea un nuevo juego en la base de datos.
    Llamada por: admin-juegos.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Juego (nombre, descripcion, rtp, min_apuesta, max_apuesta, activo) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, descripcion, rtp, min_apuesta, max_apuesta, activo)
        )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Juego creado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Admin Create Game): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  GESTIÓN DE PROMOCIONES (Ya existente)
# ==========================================================
@router.get("/api/admin/bonos")
async def api_get_all_bonos():
    """
    Obtiene la lista de todas las promociones/bonos.
    Llamada por: admin-promociones.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM Bono ORDER BY nombre_bono")
        bonos = cursor.fetchall()
        cursor.close()
        return JSONResponse({"bonos": bonos})

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Bonos): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/api/admin/bonos")
async def api_create_bono(
    nombre_bono: str = Form(),
    tipo: str = Form(),
    descripcion: str = Form(),
    valor: float = Form(),
    requisito_apuesta: float = Form(),
    fecha_expiracion: str = Form(None), # Puede ser opcional
    activo: bool = Form()
):
    """
    Crea un nuevo bono/promoción.
    Llamada por: admin-promociones.html
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        # Convertir fecha si viene, si no, es NULL
        fecha_exp = datetime.fromisoformat(fecha_expiracion) if fecha_expiracion else None

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Bono (nombre_bono, tipo, descripcion, valor, requisito_apuesta, fecha_expiracion, activo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nombre_bono, tipo, descripcion, valor, requisito_apuesta, fecha_exp, activo)
        )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True, "message": "Bono creado con éxito."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Admin Create Bono): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()
