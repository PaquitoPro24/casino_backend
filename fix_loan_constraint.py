
from app.db import db_connect

def run_migration():
    print("Iniciando migracion de constraint Transaccion...")
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            print("No se pudo conectar a la base de datos.")
            return

        cursor = conn.cursor()

        # 1. Eliminar constraint existente (necesitamos saber el nombre o intentar adivinarlo/hacerlo generico)
        # Postgres suele llamarlo tabla_columna_check. 'transaccion_tipo_transaccion_check' es el estandar.
        # "new row for relation "transaccion" violates check constraint "transaccion_tipo_transaccion_check"" <-- confirmado por el error del usuario.
        
        print("Eliminando constraint anterior...")
        cursor.execute("ALTER TABLE Transaccion DROP CONSTRAINT IF EXISTS transaccion_tipo_transaccion_check;")
        
        # 2. Agregar constraint nuevo con 'Prestamo' (y 'Préstamo' por si acaso)
        print("Agregando nuevo constraint...")
        cursor.execute("""
            ALTER TABLE Transaccion 
            ADD CONSTRAINT transaccion_tipo_transaccion_check 
            CHECK (tipo_transaccion IN ('Depósito', 'Retiro', 'Ajuste', 'Bono', 'Préstamo', 'Prestamo'));
        """)

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
