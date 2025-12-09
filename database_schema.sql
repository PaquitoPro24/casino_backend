-- ===================================================================
-- ESQUEMA COMPLETO DE BASE DE DATOS - ROYAL CRUMBS CASINO
-- ===================================================================

-- ===================================================================
-- 1. TABLA ROL
-- Se crea primero para definir los tipos de usuarios disponibles.
-- ===================================================================
CREATE TABLE IF NOT EXISTS Rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(30) UNIQUE NOT NULL, 
    descripcion TEXT
);

-- Inserción de roles base (incluyendo Agente de Soporte)
INSERT INTO Rol (nombre) VALUES 
    ('Jugador'), 
    ('Administrador'), 
    ('Auditor'),
    ('Agente de Soporte')
ON CONFLICT (nombre) DO NOTHING;

-- ===================================================================
-- 2. TABLA USUARIO
-- Se elimina la columna de texto 'rol' y se usa 'id_rol'.
-- ===================================================================
CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INTEGER NOT NULL REFERENCES Rol(id_rol) ON DELETE RESTRICT,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    curp VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ===================================================================
-- 3. TABLA SALDO (Cartera)
-- ===================================================================
CREATE TABLE IF NOT EXISTS Saldo (
    id_saldo SERIAL PRIMARY KEY,
    id_usuario INTEGER UNIQUE NOT NULL REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    saldo_actual NUMERIC(10, 2) NOT NULL CHECK (saldo_actual >= 0),
    ultima_actualizacion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===================================================================
-- 4. TABLA JUEGO
-- ===================================================================
CREATE TABLE IF NOT EXISTS Juego (
    id_juego SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    rtp NUMERIC(4, 2), -- Return To Player (%)
    min_apuesta NUMERIC(8, 2) NOT NULL,
    max_apuesta NUMERIC(8, 2) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ===================================================================
-- 5. TABLA SESION_JUEGO
-- ===================================================================
CREATE TABLE IF NOT EXISTS Sesion_Juego (
    id_sesion_juego BIGSERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    id_juego INTEGER NOT NULL REFERENCES Juego(id_juego) ON DELETE RESTRICT,
    fecha_inicio TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_fin TIMESTAMP WITHOUT TIME ZONE,
    duracion INTERVAL
);

-- ===================================================================
-- 6. TABLA APUESTA
-- ===================================================================
CREATE TABLE IF NOT EXISTS Apuesta (
    id_apuesta BIGSERIAL PRIMARY KEY,
    id_sesion_juego BIGINT NOT NULL REFERENCES Sesion_Juego(id_sesion_juego) ON DELETE CASCADE,
    monto NUMERIC(8, 2) NOT NULL,
    resultado_logica TEXT NOT NULL,
    monto_ganado NUMERIC(8, 2) NOT NULL,
    ganancia_neta NUMERIC(8, 2) NOT NULL,
    fecha_apuesta TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===================================================================
-- 7. TABLA TRANSACCION
-- ===================================================================
CREATE TABLE IF NOT EXISTS Transaccion (
    id_transaccion BIGSERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    tipo_transaccion VARCHAR(20) NOT NULL CHECK (tipo_transaccion IN ('Depósito', 'Retiro', 'Ajuste', 'Bono')),
    monto NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Pendiente', 'Completada', 'Fallida')),
    metodo_pago VARCHAR(50), 
    fecha_transaccion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===================================================================
-- 8. TABLA BONO
-- ===================================================================
CREATE TABLE IF NOT EXISTS Bono (
    id_bono SERIAL PRIMARY KEY,
    nombre_bono VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha_expiracion DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ===================================================================
-- 9. TABLA USUARIO_BONO (Relación Muchos a Muchos)
-- ===================================================================
CREATE TABLE IF NOT EXISTS Usuario_Bono (
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    id_bono INTEGER NOT NULL REFERENCES Bono(id_bono) ON DELETE CASCADE,
    fecha_adquisicion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Activo', 'Usado', 'Expirado')),
    progreso NUMERIC(3, 2) DEFAULT 0.00,
    PRIMARY KEY (id_usuario, id_bono)
);

-- ===================================================================
-- 10. TABLA SOPORTE (Tickets)
-- Lógica corregida para Jugador vs Agente
-- ===================================================================
CREATE TABLE IF NOT EXISTS Soporte (
    id_ticket SERIAL PRIMARY KEY,
    -- Usuario que reporta el problema (Jugador)
    id_jugador INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    -- Usuario que atiende el problema (Agente), puede ser NULL al inicio
    id_agente INTEGER REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    asunto VARCHAR(100) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Abierto', 'En Proceso', 'Cerrado')),
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_cierre TIMESTAMP WITHOUT TIME ZONE
);

-- ===================================================================
-- 11. TABLA METODO_PAGO
-- ===================================================================
CREATE TABLE IF NOT EXISTS Metodo_Pago (
    id_metodo SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ===================================================================
-- 12. TABLA USUARIO_METODO_PAGO (Relación Muchos a Muchos)
-- ===================================================================
CREATE TABLE IF NOT EXISTS Usuario_Metodo_Pago (
    id_metodo_usuario SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    id_metodo INTEGER NOT NULL REFERENCES Metodo_Pago(id_metodo) ON DELETE RESTRICT,
    token_externo VARCHAR(255),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- ===================================================================
-- 13. TABLA AUDITORIA
-- ===================================================================
CREATE TABLE IF NOT EXISTS Auditoria (
    id_auditoria SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario),
    fecha_auditoria TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    resumen TEXT,
    datos_auditoria JSONB NOT NULL
);

-- ===================================================================
-- 14. TABLA CHAT
-- Representa una sesión de chat entre un jugador y un agente
-- ===================================================================
CREATE TABLE IF NOT EXISTS Chat (
    id_chat SERIAL PRIMARY KEY,
    -- Usuario que inicia el chat (Jugador)
    id_jugador INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    -- Usuario que atiende el chat (Agente), puede ser NULL al inicio (en espera)
    id_agente INTEGER REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    -- Estado del chat
    estado VARCHAR(20) NOT NULL DEFAULT 'Esperando' CHECK (estado IN ('Esperando', 'Activo', 'Cerrado')),
    -- Timestamps
    fecha_inicio TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_asignacion TIMESTAMP WITHOUT TIME ZONE,
    fecha_cierre TIMESTAMP WITHOUT TIME ZONE
);

-- ===================================================================
-- 15. TABLA MENSAJE_CHAT
-- Almacena los mensajes individuales de cada chat
-- ===================================================================
CREATE TABLE IF NOT EXISTS Mensaje_Chat (
    id_mensaje BIGSERIAL PRIMARY KEY,
    id_chat INTEGER NOT NULL REFERENCES Chat(id_chat) ON DELETE CASCADE,
    -- Usuario que envía el mensaje (puede ser jugador o agente)
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    -- Indica si quien envía es el agente (TRUE) o el jugador (FALSE)
    es_agente BOOLEAN NOT NULL DEFAULT FALSE,
    -- Contenido del mensaje
    mensaje TEXT NOT NULL,
    -- Timestamp
    fecha_mensaje TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    -- Si el mensaje fue leído (opcional, para notificaciones)
    leido BOOLEAN NOT NULL DEFAULT FALSE
);

-- ===================================================================
-- CREACIÓN DE ÍNDICES (Optimización de Consultas)
-- ===================================================================

-- Usuario: Búsqueda rápida por rol
CREATE INDEX idx_usuario_rol ON Usuario (id_rol);

-- Sesion_Juego: Búsquedas por usuario o por juego
CREATE INDEX idx_sesion_juego_usuario ON Sesion_Juego (id_usuario);
CREATE INDEX idx_sesion_juego_juego ON Sesion_Juego (id_juego);

-- Apuesta: Relación con la sesión
CREATE INDEX idx_apuesta_sesion_juego ON Apuesta (id_sesion_juego);

-- Transaccion: Historial de usuario y estados
CREATE INDEX idx_transaccion_usuario ON Transaccion (id_usuario);
CREATE INDEX idx_transaccion_tipo_estado ON Transaccion (tipo_transaccion, estado);

-- Usuario_Bono: Búsquedas rápidas en la tabla pivote
CREATE INDEX idx_usuario_bono_usuario ON Usuario_Bono (id_usuario);
CREATE INDEX idx_usuario_bono_bono ON Usuario_Bono (id_bono);

-- Soporte: Búsquedas por jugador, agente o estado del ticket
CREATE INDEX idx_soporte_jugador ON Soporte (id_jugador);
CREATE INDEX idx_soporte_agente ON Soporte (id_agente);
CREATE INDEX idx_soporte_estado ON Soporte (estado);

-- Usuario_Metodo_Pago: Métodos guardados del usuario
CREATE INDEX idx_usuario_metodo_pago_usuario ON Usuario_Metodo_Pago (id_usuario);
CREATE INDEX idx_usuario_metodo_pago_metodo ON Usuario_Metodo_Pago (id_metodo);

-- Chat: Búsquedas por jugador, agente o estado
CREATE INDEX idx_chat_jugador ON Chat (id_jugador);
CREATE INDEX idx_chat_agente ON Chat (id_agente);
CREATE INDEX idx_chat_estado ON Chat (estado);

-- Mensaje_Chat: Búsquedas por chat y ordenamiento por fecha
CREATE INDEX idx_mensaje_chat_chat ON Mensaje_Chat (id_chat);
CREATE INDEX idx_mensaje_chat_fecha ON Mensaje_Chat (id_chat, fecha_mensaje);

-- ===================================================================
-- 16. TABLA RESPUESTA_TICKET
-- Almacena las respuestas de los tickets de soporte
-- ===================================================================
CREATE TABLE IF NOT EXISTS RespuestaTicket (
    id_respuesta SERIAL PRIMARY KEY,
    id_ticket INTEGER NOT NULL REFERENCES Soporte(id_ticket) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES Usuario(id_usuario) ON DELETE RESTRICT,
    mensaje TEXT NOT NULL,
    fecha_respuesta TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    es_agente BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_respuesta_ticket ON RespuestaTicket (id_ticket);
CREATE INDEX idx_respuesta_fecha ON RespuestaTicket (id_ticket, fecha_respuesta);

