import os
import psycopg2
from urllib.parse import urlparse

def get_connection():
    try:
        # 1️⃣ Leer la variable del entorno DATABASE_URL
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            # Conexión local opcional (por si pruebas en tu PC)
            return psycopg2.connect(
                host="localhost",
                database="royalcrumbs",
                user="postgres",
                password="1234"  # cambia si tienes contraseña
            )

        # 2️⃣ Parsear la URL del entorno (Render)
        parsed = urlparse(db_url)
        connection = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )

        print("✅ Conectado correctamente a la base de datos PostgreSQL")
        return connection

    except Exception as e:
        print("❌ Error al conectar a la base de datos:", e)
        return None


# ======== Prueba directa =========
if __name__ == "__main__":
    conn = get_connection()
    if conn:
        print("Conexión establecida correctamente")
        conn.close()
    else:
        print("Error al conectar")
