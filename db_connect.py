import os
import psycopg2
from urllib.parse import urlparse


def get_connection():
    try:
        # 1. Intenta leer la variable de entorno DATABASE_URL (para Render)
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            # 2. Si no existe, usa una conexión local (para tu PC)
            print("🟡 Usando conexión local a la base de datos.")
            return psycopg2.connect(
                host="localhost",
                database="royalcrumbs",  # Asegúrate que este es el nombre de tu BD local
                user="postgres",
                password="1234"  # Cambia esto por tu contraseña de Postgres
            )

        # 3. Si existe la URL, la parsea y se conecta
        print("🔵 Usando DATABASE_URL del entorno (Render).")
        parsed = urlparse(db_url)
        connection = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )
        return connection

    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

if __name__ == "__main__":
    connection = get_connection()
    if connection:
        print("✅ Conexión de prueba exitosa.")
        connection.close()
    else:
        print("❌ Falló la conexión de prueba.")
