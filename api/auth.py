from fastapi import APIRouter, Form
# ... (código existente) ...
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
# ... (código existente) ...
@router.post("/api/auth/register")
async def api_register(
# ... (código existente) ...
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ==========================================================
#  NUEVA RUTA: RECUPERAR CONTRASEÑA (SIMULACIÓN)
# ==========================================================
@router.post("/api/auth/forgot-password")
async def api_forgot_password(correo: str = Form()):
    """
    Ruta para manejar la solicitud de "Olvidé mi contraseña".
    Llamada por: forgot_password.html
    """
    print(f"🔹 API: Solicitud de recuperación de contraseña para: {correo}")
    
    conn = None
    cursor = None
    
    try:
        conn = db_connect.get_connection()
        if conn is None:
            # No le digas al usuario que la BD falló, solo da el mensaje genérico
            return JSONResponse({"message": "Si este correo está registrado, recibirás un enlace de recuperación."})
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Buscamos al usuario
        cursor.execute("SELECT id_usuario FROM Usuario WHERE email = %s AND activo = true", (correo,))
        usuario = cursor.fetchone()
        
        # 2. SIMULACIÓN
        if usuario:
            # --- INICIO DE SIMULACIÓN ---
            # En un proyecto real, aquí generarías un token, lo guardarías en la BD
            # y lo enviarías por email.
            # Por ahora, solo lo imprimimos en la consola del servidor.
            token_simulado = "TOKEN_SEGURO_GENERADO_AQUI_12345"
            print(f"✅ API: SIMULACIÓN - Enviando email de reseteo a {correo} con token: {token_simulado}")
            # --- FIN DE SIMULACIÓN ---
        else:
            print(f"❌ API: Solicitud de reseteo para email no existente o inactivo: {correo}")

        # 3. RESPUESTA GENÉRICA
        # Por seguridad, NUNCA le digas al usuario si el correo existía o no.
        # Siempre devuelve el mismo mensaje de éxito.
        return JSONResponse({"success": True, "message": "Si este correo está registrado en nuestro sistema, recibirás un enlace para recuperar tu contraseña."})

    except Exception as e:
        print(f"🚨 API ERROR (Forgot Password): {e}")
        # Incluso si hay un error, devolvemos el mensaje genérico
        return JSONResponse({"message": "Si este correo está registrado, recibirás un enlace de recuperación."})
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        
        # 1. Usamos los nombres correctos: 'Usuario', 'email', 'password_hash'
        cursor.execute(
            "SELECT id_usuario, rol, password_hash, activo FROM Usuario WHERE email = %s", 
            (correo,)
        )
        usuario = cursor.fetchone()
        
        # 2. Verificar si el usuario existe y está activo
        if not usuario:
            print("❌ API: Email no encontrado")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)
        
        if not usuario["activo"]:
            print("❌ API: Cuenta inactiva")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Esta cuenta ha sido desactivada"}, status_code=403)

        # 3. Verificamos la contraseña (usando 'password_hash')
        # passlib detectará automáticamente que el hash es Argon2
        if not pwd_context.verify(contrasena, usuario["password_hash"]):
            print("❌ API: Contraseña incorrecta")
            cursor.close(); conn.close()
            return JSONResponse({"error": "Correo o contraseña incorrectos"}, status_code=401)
        
        # 4. ¡Éxito!
        cursor.close(); conn.close()
        
        print(f"✅ API: Login exitoso para {usuario['id_usuario']}")
        return JSONResponse({
            "id_usuario": usuario['id_usuario'],
            "rol": usuario['rol'] # Tu BD usa 'Jugador', 'Administrador'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Login): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    finally:
        if conn: conn.close()


# ==========================================================
#  RUTA PARA REGISTRO (Ahora usará Argon2)
# ==========================================================
@router.post("/api/auth/register")
async def api_register(
    correo: str = Form(),
    curp: str = Form(), 
    nombre: str = Form(),
    apellido: str = Form(),
    contrasena: str = Form()
):
    """
    Ruta de Registro, actualizada a tu esquema 'Usuario' y 'Saldo'
    """
    print(f"🔹 API: Intento de registro para: {correo}")
    conn = None
    cursor = None
    
    try:
        # 1. Hashear la contraseña (ahora con Argon2)
        hashed_password = pwd_context.hash(contrasena)
        
        # 2. Conectarse a la BD
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        
        # 3. PASO 1: Insertar en la tabla 'Usuario'
        cursor.execute(
            """
            INSERT INTO Usuario (nombre, apellido, curp, email, password_hash, rol, fecha_registro, activo)
            VALUES (%s, %s, %s, %s, %s, 'Jugador', %s, true)
            RETURNING id_usuario
            """,
            (nombre, apellido, curp, correo, hashed_password, datetime.now())
        )
        
        # Obtenemos el ID del usuario que acabamos de crear
        new_user_id = cursor.fetchone()[0]
        
        # 4. PASO 2: Insertar en la tabla 'Saldo'
        cursor.execute(
            """
            INSERT INTO Saldo (id_usuario, saldo_actual, ultima_actualizacion)
            VALUES (%s, 0.00, %s)
            """,
            (new_user_id, datetime.now())
        )
        
        # 5. Confirmar la transacción (ambos inserts)
        conn.commit()
        
        print(f"✅ API: Registro exitoso para {correo}, ID: {new_user_id}")
        return JSONResponse({"success": True, "message": "Usuario registrado exitosamente"})

    except psycopg2.errors.UniqueViolation as e:
        if conn: conn.rollback()
        print(f"❌ API: Conflicto de datos (email o curp ya existen): {e}")
        return JSONResponse({"error": "El correo electrónico o la CURP ya están registrados."}, status_code=409)
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"🚨 API ERROR (Register): {e}")
        return JSONResponse({"error": f"Error interno del servidor: {e}"}, status_code=500)
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
