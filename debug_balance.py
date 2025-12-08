from app.db import db_connect

def check_balance(user_id):
    conn = db_connect.get_connection()
    if not conn:
        print("No DB connection")
        return

    cur = conn.cursor()
    cur.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (user_id,))
    res = cur.fetchone()
    print(f"User {user_id} Balance: {res[0] if res else 'No record found'}")
    conn.close()

if __name__ == "__main__":
    check_balance(9)
