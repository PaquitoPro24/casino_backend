
import psycopg2
from app.db import db_connect

def seed_games():
    print("Verificando juegos iniciales...")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            print("Error: No se pudo conectar a la base de datos.")
            return

        cursor = conn.cursor()

        # Lista de juegos a asegurar
        # (Nombre, Descripcion, RTP, Min, Max, Activo)
        default_games = [
            ("Ruleta Europea", "Clasica ruleta con un solo cero.", 97.30, 1.00, 5000.00, True),
            ("Blackjack", "Juego de cartas contra el dealer.", 99.50, 5.00, 1000.00, True),
            ("Tragamonedas Neon", "Slot machine tematica neon.", 95.00, 0.50, 100.00, True)
        ]

        for game in default_games:
            nombre, desc, rtp, min_bet, max_bet, active = game
            
            # Verificar si existe
            cursor.execute("SELECT id_juego FROM Juego WHERE nombre = %s", (nombre,))
            res = cursor.fetchone()
            
            if res:
                print(f"Juego '{nombre}' ya existe.")
            else:
                print(f"Agregando juego '{nombre}'...")
                cursor.execute(
                    """
                    INSERT INTO Juego (nombre, descripcion, rtp, min_apuesta, max_apuesta, activo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (nombre, desc, rtp, min_bet, max_bet, active)
                )

        conn.commit()
        print("Juegos verificados correctamente.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"Error al sembrar juegos: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    seed_games()
