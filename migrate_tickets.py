
from app.db import db_connect
import psycopg2

def run_migration():
    print("Iniciando migracion de base de datos...")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            print("No se pudo conectar a la base de datos.")
            return

        cursor = conn.cursor()

        # Crear tabla RespuestaTicket
        print("Creando tabla RespuestaTicket...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RespuestaTicket (
                id_respuesta SERIAL PRIMARY KEY,
                id_ticket INTEGER NOT NULL REFERENCES Soporte(id_ticket) ON DELETE CASCADE,
                id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
                mensaje TEXT NOT NULL,
                fecha_respuesta TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                es_agente BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
        
        # Crear índices
        print("Creando indices...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_respuesta_ticket ON RespuestaTicket (id_ticket);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_respuesta_fecha ON RespuestaTicket (id_ticket, fecha_respuesta);")

        conn.commit()
        print("Migracion completada con exito.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error durante la migracion: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
