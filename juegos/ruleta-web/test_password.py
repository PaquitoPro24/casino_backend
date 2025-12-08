#!/usr/bin/env python3
"""
Script para generar password hashes con Argon2
Compatible con el sistema de autenticación de la ruleta web
"""

from passlib.context import CryptContext

# Configurar Argon2 (mismo esquema que auth.py)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def generar_hash(password: str) -> str:
    """Genera un hash Argon2 para el password dado"""
    return pwd_context.hash(password)

def verificar_password(password: str, hash: str) -> bool:
    """Verifica si un password coincide con un hash"""
    return pwd_context.verify(password, hash)

if __name__ == "__main__":
    print("=" * 60)
    print("GENERADOR DE PASSWORD HASH - RULETA WEB")
    print("=" * 60)
    print()
    
    # Opción 1: Generar nuevo hash
    print("1. GENERAR NUEVO HASH")
    print("-" * 60)
    password = input("Ingresa el password a hashear: ")
    
    if password:
        hash_generado = generar_hash(password)
        print("\n✅ Hash generado exitosamente:")
        print(f"\nPassword: {password}")
        print(f"Hash:     {hash_generado}")
        print("\nCopia este hash en tu INSERT INTO usuario:")
        print(f"password_hash = '{hash_generado}'")
        
        # Verificar que funciona
        print("\n" + "=" * 60)
        print("2. VERIFICACIÓN")
        print("-" * 60)
        if verificar_password(password, hash_generado):
            print("✅ Verificación exitosa - El hash funciona correctamente")
        else:
            print("❌ Error en la verificación")
    
    print("\n" + "=" * 60)
    print("EJEMPLO DE SQL PARA INSERTAR USUARIO:")
    print("=" * 60)
    print(f"""
INSERT INTO usuario (id_rol, nombre, apellido, curp, email, password_hash, activo)
VALUES (
    1,
    'Nombre',
    'Apellido',
    'CURP000101HDFRNN01',
    'email@example.com',
    '{hash_generado if password else "$argon2id$..."}',
    true
);

INSERT INTO saldo (id_usuario, saldo_actual)
SELECT id_usuario, 500.00
FROM usuario
WHERE email = 'email@example.com';
    """)
    
    print("=" * 60)
    print("\n¡Listo! Usa este SQL en tu base de datos de Render.")
