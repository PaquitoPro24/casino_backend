import psycopg2
import os

# Esta línea mágica obtiene la URL de la variable de entorno que creaste en Render
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    try:
        # Se conecta usando la URL del entorno
        connection = psycopg2.connect(DATABASE_URL)
        return connection
    except (Exception, psycopg2.DatabaseError) as error:
        print("❌ Error al conectar a PostgreSQL:", error)
        return None

# ======================================
# ✅ PRUEBA DE CONEXIÓN
# ======================================
if __name__ == "__main__":
    connection = get_connection()
    if connection:
        print("✅ Conexión a PostgreSQL establecida correctamente")
        connection.close()
    else:
        print("❌ Error: no se pudo conectar a la base de datos")
