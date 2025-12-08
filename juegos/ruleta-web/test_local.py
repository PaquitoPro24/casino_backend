#!/usr/bin/env python3
"""
Script de prueba local para verificar la conexión a PostgreSQL
Ejecuta este script para validar tu configuración antes de desplegar
"""

import os
import sys

def test_imports():
    """Verificar que todas las dependencias estén instaladas"""
    print("=" * 60)
    print("1. VERIFICANDO DEPENDENCIAS")
    print("=" * 60)
    
    dependencias = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("psycopg2", "psycopg2-binary"),
        ("jose", "python-jose"),
        ("passlib", "passlib"),
    ]
    
    faltan = []
    for modulo, nombre in dependencias:
        try:
            __import__(modulo)
            print(f"✅ {nombre}")
        except ImportError:
            print(f"❌ {nombre} - NO INSTALADO")
            faltan.append(nombre)
    
    if faltan:
        print(f"\n⚠️ Faltan dependencias: {', '.join(faltan)}")
        print("Ejecuta: pip install -r requirements.txt")
        return False
    
    print("\n✅ Todas las dependencias instaladas correctamente")
    return True

def test_database_url():
    """Verificar que DATABASE_URL esté configurada"""
    print("\n" + "=" * 60)
    print("2. VERIFICANDO DATABASE_URL")
    print("=" * 60)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL no está configurada")
        print("\nConfigúrala con:")
        print('  PowerShell: $env:DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"')
        print('  Bash:       export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"')
        return False
    
    print(f"✅ DATABASE_URL configurada")
    print(f"   Conexión: {db_url[:30]}..." if len(db_url) > 30 else f"   Conexión: {db_url}")
    
    # Verificar fix de postgres:// -> postgresql://
    if db_url.startswith("postgres://") and not db_url.startswith("postgresql://"):
        print("ℹ️  Nota: Se aplicará fix automático postgres:// → postgresql://")
    
    return True

def test_database_connection():
    """Intentar conectar a la base de datos"""
    print("\n" + "=" * 60)
    print("3. PROBANDO CONEXIÓN A POSTGRESQL")
    print("=" * 60)
    
    try:
        from database import test_connection
        if test_connection():
            print("✅ Conexión exitosa a PostgreSQL")
            return True
        else:
            print("❌ No se pudo conectar a PostgreSQL")
            return False
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return False

def test_tables():
    """Verificar que las tablas existan"""
    print("\n" + "=" * 60)
    print("4. VERIFICANDO TABLAS EN LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        from database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tablas_requeridas = ['rol', 'usuario', 'saldo']
        tablas_existentes = inspector.get_table_names()
        
        for tabla in tablas_requeridas:
            if tabla in tablas_existentes:
                print(f"✅ Tabla '{tabla}' existe")
            else:
                print(f"❌ Tabla '{tabla}' NO EXISTE")
                print(f"   Ejecuta create_tables.sql en tu base de datos")
        
        return all(t in tablas_existentes for t in tablas_requeridas)
    except Exception as e:
        print(f"❌ Error al verificar tablas: {e}")
        return False

def test_models():
    """Verificar que los modelos ORM funcionen"""
    print("\n" + "=" * 60)
    print("5. VERIFICANDO MODELOS ORM")
    print("=" * 60)
    
    try:
        from models import Usuario, Rol, Saldo
        from database import SessionLocal
        
        db = SessionLocal()
        
        # Contar registros
        num_roles = db.query(Rol).count()
        num_usuarios = db.query(Usuario).count()
        num_saldos = db.query(Saldo).count()
        
        print(f"✅ Roles en BD: {num_roles}")
        print(f"✅ Usuarios en BD: {num_usuarios}")
        print(f"✅ Saldos en BD: {num_saldos}")
        
        if num_usuarios == 0:
            print("\n⚠️ No hay usuarios creados. Usa test_password.py para crear uno.")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error en modelos ORM: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "=" * 60)
    print("PRUEBA LOCAL - RULETA WEB CON POSTGRESQL")
    print("=" * 60 + "\n")
    
    # Ejecutar pruebas en orden
    resultados = [
        test_imports(),
        test_database_url(),
    ]
    
    # Si las primeras 2 pasan, continuar con las que requieren BD
    if all(resultados):
        resultados.append(test_database_connection())
        resultados.append(test_tables())
        resultados.append(test_models())
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if all(resultados):
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("\n¡Tu aplicación está lista para ejecutarse!")
        print("\nEjecuta: uvicorn app:app --reload")
        print("Abre:    http://localhost:8000")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\nRevisa los errores arriba y corrígelos antes de continuar.")
    
    print("=" * 60 + "\n")
    
    return all(resultados)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nPrueba interrumpida por el usuario.")
        sys.exit(1)
