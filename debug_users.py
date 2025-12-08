import asyncio
from app.db import db_connect
import psycopg2
from psycopg2.extras import RealDictCursor

def check_user_count():
    print("--- DEBUG USER COUNT ---")
    conn = db_connect.get_connection()
    if not conn:
        print("Failed to connect to DB")
        return

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Total users
    cursor.execute("SELECT COUNT(*) as total FROM Usuario")
    total_raw = cursor.fetchone()['total']
    print(f"Total entries in Usuario table: {total_raw}")

    # 2. Users by Role
    cursor.execute("SELECT id_rol, COUNT(*) as count FROM Usuario GROUP BY id_rol")
    roles = cursor.fetchall()
    print("Users by Role ID:")
    for r in roles:
        print(f"  Role ID {r['id_rol']}: {r['count']}")

    # 3. List Users with Role 1 (Player)
    cursor.execute("SELECT id_usuario, nombre, email, id_rol FROM Usuario WHERE id_rol = 1")
    users = cursor.fetchall()
    print("\nUsers with Role 1 (Player):")
    for u in users:
        print(f"  ID: {u['id_usuario']}, Name: {u['nombre']}, Email: {u['email']}, Role: {u['id_rol']}")

    conn.close()

if __name__ == "__main__":
    check_user_count()
