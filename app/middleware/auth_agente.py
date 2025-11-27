from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor

async def verificar_rol_agente(request: Request):
    """
    Middleware para verificar que el usuario tenga rol 'Agente de Soporte' (id_rol = 4)
    Retorna el id_usuario si es válido, de lo contrario lanza HTTPException
    """
    # Intentar obtener user_id de las cookies o headers
    user_id = request.cookies.get("userId")
    
    if not user_id:
        # Si no hay cookie, intentar obtener del header (para APIs)
        user_id = request.headers.get("X-User-Id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID de usuario inválido"
        )
    
    # Verificar en la base de datos que el usuario tenga id_rol = 4 (Agente de Soporte)
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de conexión a la base de datos"
            )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT u.id_usuario, u.id_rol, u.activo, r.nombre as rol_nombre
            FROM Usuario u
            JOIN Rol r ON u.id_rol = r.id_rol
            WHERE u.id_usuario = %s
            """,
            (user_id,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        if not usuario['activo']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Verificar que sea Agente de Soporte (id_rol = 4)
        if usuario['id_rol'] != 4:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Se requiere rol de Agente de Soporte"
            )
        
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🚨 Error en verificar_rol_agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar permisos"
        )
    finally:
        if conn:
            conn.close()


async def verificar_rol_agente_redirect(request: Request):
    """
    Versión del middleware que redirige al login en lugar de lanzar HTTPException
    Útil para rutas HTML
    """
    user_id = request.cookies.get("userId")
    
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        user_id = int(user_id)
    except ValueError:
        return RedirectResponse(url="/login", status_code=302)
    
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return RedirectResponse(url="/login", status_code=302)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT u.id_usuario, u.id_rol, u.activo
            FROM Usuario u
            WHERE u.id_usuario = %s
            """,
            (user_id,)
        )
        usuario = cursor.fetchone()
        cursor.close()
        
        # Verificar que el usuario existe, está activo y tiene id_rol = 4 (Agente de Soporte)
        if not usuario or not usuario['activo'] or usuario['id_rol'] != 4:
            return RedirectResponse(url="/login", status_code=302)
        
        return None  # Todo OK, continuar
        
    except Exception as e:
        print(f"🚨 Error en verificar_rol_agente_redirect: {e}")
        return RedirectResponse(url="/login", status_code=302)
    finally:
        if conn:
            conn.close()
