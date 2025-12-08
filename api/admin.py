from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import db_connect # <-- CORRECCIÓN: Importación relativa
import psycopg2
from psycopg2.extras import RealDictCursor
import decimal # Importamos decimal para manejar dinero
from datetime import datetime # Para manejar fechas
from passlib.context import CryptContext

# Configura el contexto de hasheo (mismo que auth.py)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/api/admin", tags=["Admin"])

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
        cursor.execute("SELECT COUNT(*) as total FROM Usuario WHERE id_rol = 1")
        total_users = cursor.fetchone()['total']
        
        # 2. Usuarios Activos (jugadores activos)
        cursor.execute("SELECT COUNT(*) as active FROM Usuario WHERE id_rol = 1 AND activo = true")
        active_users = cursor.fetchone()['active']
        
        # 3. Depósitos Totales (Histórico)
        cursor.execute(
            "SELECT COALESCE(SUM(monto), 0) as total FROM Transaccion WHERE tipo_transaccion = 'Depósito' AND estado = 'Completada'"
        )
        total_deposits = cursor.fetchone()['total']

        # 4. Retiros Totales (Histórico)
        cursor.execute(
            "SELECT COALESCE(SUM(monto), 0) as total FROM Transaccion WHERE tipo_transaccion = 'Retiro' AND estado = 'Completada'"
        )
        total_withdrawals = cursor.fetchone()['total']
        
        cursor.close()
        
        return JSONResponse({
            "total_users": total_users,
            "active_users": active_users,
            "total_deposits": float(total_deposits),
            "total_withdrawals": float(total_withdrawals)
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
        
        # Buscamos solo Jugadores (id_rol = 1)
        cursor.execute(
            """
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, u.activo, r.nombre as rol
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE u.id_rol = 1
            ORDER BY u.nombre
            """
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
        
        # Buscamos Admins (id_rol = 2) y Auditores (id_rol = 3)
        cursor.execute(
            """
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, r.nombre as rol, u.activo
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE u.id_rol IN (2, 3)
            ORDER BY u.nombre
            """
        )
        admins = cursor.fetchall()
        cursor.close()
        
        return JSONResponse({"admins": admins})

    except Exception as e:
        print(f"🚨 API ERROR (Admin Get Admins): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/api/admin/administradores")
async def api_create_admin(
    nombre: str = Form(),
    apellido: str = Form(),
    email: str = Form(),
    password: str = Form(),
    rol: str = Form()
):
    """
    Crea un nuevo administrador o auditor.
    Llamada por: admin-administrador-perfil.html
    """
    print(f"🔹 API Admin: Creando nuevo administrador: {email} ({rol})")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()

        # 1. Obtener ID del rol
        cursor.execute("SELECT id_rol FROM Rol WHERE nombre = %s", (rol,))
        rol_res = cursor.fetchone()
        if not rol_res:
            return JSONResponse({"error": "Rol no válido"}, status_code=400)
        id_rol = rol_res[0]

        # 2. Hashear password
        hashed_password = pwd_context.hash(password)

        # 3. Insertar Usuario
        cursor.execute(
            """
            INSERT INTO Usuario (nombre, apellido, email, password_hash, id_rol, fecha_registro, activo)
            VALUES (%s, %s, %s, %s, %s, %s, true)
            RETURNING id_usuario
            """,
            (nombre, apellido, email, hashed_password, id_rol, datetime.now())
        )
        new_id = cursor.fetchone()[0]

        # 4. Insertar Saldo inicial (aunque sea admin, por integridad)
        cursor.execute(
            "INSERT INTO Saldo (id_usuario, saldo_actual, ultima_actualizacion) VALUES (%s, 0.00, %s)",
            (new_id, datetime.now())
        )

        conn.commit()
        cursor.close()
        
        return JSONResponse({"success": True, "message": "Administrador creado con éxito."})

    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        return JSONResponse({"error": "El correo ya está registrado."}, status_code=409)
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Create Admin): {e}")
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
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, r.nombre as rol, u.activo, u.fecha_registro, s.saldo_actual
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
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
        
        # Convertir fecha a string (ISO format) para evitar error de serialización
        if user_profile.get('fecha_registro'):
            user_profile['fecha_registro'] = user_profile['fecha_registro'].isoformat()
            
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
        
        # Primero obtenemos el id_rol correspondiente al nombre del rol
        cursor.execute("SELECT id_rol FROM Rol WHERE nombre = %s", (rol,))
        rol_result = cursor.fetchone()
        if not rol_result:
            return JSONResponse({" error": "Rol inválido"}, status_code=400)
        id_rol = rol_result[0]
        
        # Ahora actualizamos con id_rol
        cursor.execute(
            "UPDATE Usuario SET nombre = %s, apellido = %s, email = %s, id_rol = %s, activo = %s WHERE id_usuario = %s",
            (nombre, apellido, email, id_rol, activo, id_usuario)
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
            "INSERT INTO Bono (nombre_bono, tipo, descripcion, fecha_expiracion, activo) VALUES (%s, %s, %s, %s, %s)",
            (nombre_bono, tipo, descripcion, fecha_exp, activo)
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

@router.delete("/api/admin/bonos/{id_bono}")
async def api_delete_bono(id_bono: int):
    """
    Elimina un bono.
    """
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Bono WHERE id_bono = %s", (id_bono,))
        conn.commit()
        cursor.close()
        
        return JSONResponse({"success": True, "message": "Bono eliminado."})

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Admin Delete Bono): {e}")
        return JSONResponse({"error": f"Error interno: {e}"}, status_code=500)
    finally:
        if conn: conn.close()

# ==========================================================
#  CONFIGURACIÓN (Bloqueo IP)
# ==========================================================
def ensure_ip_table():
    """Crea la tabla BloqueoIP si no existe."""
    conn = None
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BloqueoIP (
                id_bloqueo SERIAL PRIMARY KEY,
                ip_address VARCHAR(50) UNIQUE NOT NULL,
                razon TEXT,
                fecha_bloqueo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT TRUE
            );
        """)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error creating BloqueoIP table: {e}")
    finally:
        if conn: conn.close()

# Llamamos a esto al iniciar (o al primer request, simplicidad aquí)
ensure_ip_table()

@router.get("/api/admin/config/ip-block")
async def api_get_blocked_ips():
    conn = None
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM BloqueoIP ORDER BY fecha_bloqueo DESC")
        ips = cursor.fetchall()
        cursor.close()
        return JSONResponse({"ips": ips})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn: conn.close()

@router.post("/api/admin/config/ip-block")
async def api_block_ip(ip_address: str = Form(), razon: str = Form("")):
    conn = None
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO BloqueoIP (ip_address, razon) VALUES (%s, %s)",
            (ip_address, razon)
        )
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True})
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        return JSONResponse({"error": "La IP ya está bloqueada."}, status_code=409)
    except Exception as e:
        if conn: conn.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn: conn.close()

@router.delete("/api/admin/config/ip-block/{id_bloqueo}")
async def api_unblock_ip(id_bloqueo: int):
    conn = None
    try:
        conn = db_connect.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM BloqueoIP WHERE id_bloqueo = %s", (id_bloqueo,))
        conn.commit()
        cursor.close()
        return JSONResponse({"success": True})
    except Exception as e:
        if conn: conn.rollback()
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if conn: conn.close()
