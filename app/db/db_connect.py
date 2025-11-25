import os
import psycopg2
from urllib.parse import urlparse

def get_connection():
    """
    Establece conexión con PostgreSQL usando DATABASE_URL del archivo .env
    o credenciales locales si no está configurada.
    """
    try:
        # 1️⃣ Leer la variable del entorno DATABASE_URL
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            print("⚠️ WARNING: DATABASE_URL no encontrada en .env")
            print("⚠️ Intentando conexión local con credenciales por defecto...")
            print("⚠️ Si esto falla, configura DATABASE_URL en el archivo .env")
            
            # Conexión local opcional (por si pruebas en tu PC)
            connection = psycopg2.connect(
                host="localhost",
                database="royalcrumbs",
                user="postgres",
                password="1234"
            )
            print("✅ Conectado a base de datos LOCAL")
            return connection

        # 2️⃣ Parsear la URL del entorno (Neon.tech/Render)
        print(f"🔹 Intentando conectar a base de datos remota...")
        parsed = urlparse(db_url)
        
        # Construir parámetros de conexión
        conn_params = {
            "host": parsed.hostname,
            "database": parsed.path.lstrip("/"),
            "user": parsed.username,
            "password": parsed.password,
            "port": parsed.port or 5432
        }
        
        # Neon.tech requiere SSL
        if "neon.tech" in str(parsed.hostname):
            conn_params["sslmode"] = "require"
        
        connection = psycopg2.connect(**conn_params)
        print(f"✅ Conectado correctamente a la base de datos PostgreSQL")
        print(f"   Host: {parsed.hostname}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        return connection

    except psycopg2.OperationalError as e:
        print("❌ ERROR DE CONEXIÓN A LA BASE DE DATOS:")
        print(f"   {e}")
        print("\n🔍 POSIBLES CAUSAS:")
        print("   1. DATABASE_URL incorrecta en el archivo .env")
        print("   2. Credenciales inválidas")
        print("   3. Base de datos no accesible (firewall/red)")
        print("   4. SSL requerido pero no configurado")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al conectar a la base de datos: {e}")
        return None


# ======== Prueba directa =========
if __name__ == "__main__":
    conn = get_connection()
    if conn:
        print("Conexión establecida correctamente")
        conn.close()
    else:
        print("Error al conectar")
