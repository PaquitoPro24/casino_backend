# db_config.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def get_db_connection():
    """Crea y retorna una conexión a PostgreSQL en Neon.tech."""
    try:
        # URL de conexión de Neon.tech (formato: postgresql://user:password@host/database)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            conn = psycopg2.connect(database_url)
        else:
            # Fallback para desarrollo local
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'casino_db'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', ''),
                port=os.environ.get('DB_PORT', '5432')
            )
        return conn
    except Exception as e:
        print(f"⚠ Error al conectar a PostgreSQL: {e}")
        return None

def get_user_balance(user_id):
    """
    Obtiene el saldo actual del usuario desde PostgreSQL.
    Busca en la tabla Usuario por email (user_id) y luego en Saldo.
    
    Args:
        user_id: El email del usuario (usado como identificador desde App Inventor)
        
    Returns:
        int: El saldo actual, o 500 si no existe o hay error
    """
    conn = get_db_connection()
    if not conn:
        return 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar el usuario por email y obtener su saldo
        cursor.execute("""
            SELECT s.saldo_actual 
            FROM Usuario u
            JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.email = %s AND u.activo = true
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['saldo_actual'] is not None:
            return int(result['saldo_actual'])
        else:
            # Usuario no encontrado o sin saldo
            print(f"⚠ Usuario {user_id} no encontrado o sin saldo")
            return 500
    except Exception as e:
        print(f"⚠ Error al leer saldo de PostgreSQL: {e}")
        if conn:
            conn.close()
        return 500

def update_user_balance(user_id, new_balance):
    """
    Actualiza el saldo del usuario en PostgreSQL.
    Actualiza la tabla Saldo basándose en el email del usuario.
    
    Args:
        user_id: El email del usuario
        new_balance: El nuevo saldo a guardar
        
    Returns:
        bool: True si se actualizó correctamente, False si hubo error
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Actualizar saldo del usuario
        cursor.execute("""
            UPDATE Saldo 
            SET saldo_actual = %s, 
                ultima_actualizacion = %s
            WHERE id_usuario = (
                SELECT id_usuario 
                FROM Usuario 
                WHERE email = %s AND activo = true
            )
        """, (float(new_balance), datetime.now(), user_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            return True
        else:
            print(f"⚠ No se pudo actualizar saldo para usuario {user_id}")
            return False
    except Exception as e:
        print(f"⚠ Error al actualizar saldo en PostgreSQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def registrar_usuario_nuevo(datos):
    """
    Registra un nuevo usuario en PostgreSQL.
    
    Args:
        datos: Diccionario con nombre, apellido, curp, email, password, direccion, rci, ingresos
        
    Returns:
        dict: {"exito": bool, "mensaje": str, "id_usuario": int}
    """
    import hashlib
    
    conn = get_db_connection()
    if not conn:
        return {"exito": False, "mensaje": "Error de conexión a BD"}
    
    try:
        cursor = conn.cursor()
        
        # Encriptar contraseña (SHA256)
        pass_hash = hashlib.sha256(datos['password'].encode()).hexdigest()
        
        # Insertar en tabla Usuario
        sql_usuario = """
            INSERT INTO Usuario (nombre, apellido, curp, email, password_hash, rol, fecha_registro, activo)
            VALUES (%s, %s, %s, %s, %s, 'Jugador', NOW(), true)
            RETURNING id_usuario;
        """
        cursor.execute(sql_usuario, (
            datos.get('nombre', ''),
            datos.get('apellido', ''),
            datos.get('curp', ''),
            datos['email'],
            pass_hash
        ))
        id_nuevo = cursor.fetchone()[0]
        
        # Crear Saldo inicial
        sql_saldo = """
            INSERT INTO Saldo (id_usuario, saldo_actual, ultima_actualizacion)
            VALUES (%s, 500, NOW());
        """
        cursor.execute(sql_saldo, (id_nuevo,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "exito": True, 
            "mensaje": "Usuario registrado correctamente",
            "id_usuario": id_nuevo
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"⚠ Error al registrar usuario: {e}")
        return {
            "exito": False, 
            "mensaje": f"Error al registrar: {str(e)}"
        }

def verificar_usuario(email, password):
    """
    Verifica las credenciales del usuario.
    
    Args:
        email: Email del usuario
        password: Contraseña en texto plano
        
    Returns:
        dict: {"exito": bool, "mensaje": str, "usuario": dict}
    """
    import hashlib
    
    conn = get_db_connection()
    if not conn:
        return {"exito": False, "mensaje": "Error de conexión a BD"}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Encriptar contraseña ingresada
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Buscar usuario con email y contraseña
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.email, u.rol, s.saldo_actual
            FROM Usuario u
            LEFT JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.email = %s AND u.password_hash = %s AND u.activo = true
        """, (email, pass_hash))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if usuario:
            return {
                "exito": True,
                "mensaje": "Login exitoso",
                "usuario": {
                    "id_usuario": usuario['id_usuario'],
                    "nombre": usuario['nombre'],
                    "apellido": usuario['apellido'],
                    "email": usuario['email'],
                    "rol": usuario['rol'],
                    "saldo": int(usuario['saldo_actual']) if usuario['saldo_actual'] else 0
                }
            }
        else:
            return {
                "exito": False,
                "mensaje": "Email o contraseña incorrectos"
            }
            
    except Exception as e:
        if conn:
            conn.close()
        print(f"⚠ Error al verificar usuario: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al verificar: {str(e)}"
        }
