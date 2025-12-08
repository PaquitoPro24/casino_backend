-- =====================================================
-- SCRIPT DE CREACIÓN DE TABLAS PARA RULETA WEB
-- =====================================================
-- Ejecuta este script en tu base de datos PostgreSQL de Render
-- =====================================================

-- Tabla de Roles
CREATE TABLE IF NOT EXISTS rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(30) UNIQUE NOT NULL,
    descripcion TEXT
);

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INTEGER REFERENCES rol(id_rol) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    curp VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de Saldos
CREATE TABLE IF NOT EXISTS saldo (
    id_saldo SERIAL PRIMARY KEY,
    id_usuario INTEGER UNIQUE REFERENCES usuario(id_usuario) NOT NULL,
    saldo_actual NUMERIC(10, 2) DEFAULT 500.00 NOT NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar Roles por Defecto
INSERT INTO rol (nombre, descripcion) VALUES 
    ('jugador', 'Usuario regular del casino'),
    ('admin', 'Administrador del sistema')
ON CONFLICT (nombre) DO NOTHING;

-- =====================================================
-- DATOS DE PRUEBA (OPCIONAL)
-- =====================================================
-- Descomenta las siguientes líneas para crear un usuario de prueba
-- NOTA: Necesitas generar el password_hash primero

/*
-- Usuario de prueba: test@example.com
-- Password: test123
-- Hash generado con Argon2 (genera el tuyo con el script test_password.py)

INSERT INTO usuario (id_rol, nombre, apellido, curp, email, password_hash, activo)
VALUES (
    1,
    'Test',
    'Usuario',
    'TEST000101HDFRNN01',
    'test@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$REEMPLAZA_CON_TU_HASH',
    true
) ON CONFLICT (email) DO NOTHING;

-- Crear saldo inicial para el usuario de prueba
INSERT INTO saldo (id_usuario, saldo_actual)
SELECT id_usuario, 500.00
FROM usuario
WHERE email = 'test@example.com'
ON CONFLICT (id_usuario) DO NOTHING;
*/

-- =====================================================
-- VERIFICACIÓN
-- =====================================================
-- Ejecuta estas consultas para verificar que todo esté correcto

-- Ver todos los roles
SELECT * FROM rol;

-- Ver todos los usuarios
SELECT u.id_usuario, u.nombre, u.apellido, u.email, r.nombre as rol, u.activo
FROM usuario u
JOIN rol r ON u.id_rol = r.id_rol;

-- Ver saldos
SELECT u.email, s.saldo_actual, s.ultima_actualizacion
FROM saldo s
JOIN usuario u ON s.id_usuario = u.id_usuario;

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
