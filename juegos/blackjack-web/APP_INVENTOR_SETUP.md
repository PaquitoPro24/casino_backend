# Guía de Integración App Inventor con PostgreSQL (Sin Firebase)

## Sistema Completo de Autenticación

Tu aplicación ahora usa **100% PostgreSQL** para autenticación y gestión de usuarios.

---

## 📋 APIs Disponibles

### 1. **Registro de Usuario**
**Endpoint**: `POST /api/registrar`

**Body (JSON)**:
```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "curp": "JUAP900101HDFRNN01",
  "email": "juan@email.com",
  "password": "mipassword123"
}
```

**Respuesta Exitosa**:
```json
{
  "exito": true,
  "mensaje": "Usuario registrado correctamente",
  "id_usuario": 123
}
```

**Respuesta Error**:
```json
{
  "exito": false,
  "mensaje": "Error al registrar: ..."
}
```

---

### 2. **Login de Usuario**
**Endpoint**: `POST /api/login_usuario`

**Body (JSON)**:
```json
{
  "email": "juan@email.com",
  "password": "mipassword123"
}
```

**Respuesta Exitosa**:
```json
{
  "exito": true,
  "mensaje": "Login exitoso",
  "usuario": {
    "id_usuario": 123,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@email.com",
    "rol": "Jugador",
    "saldo": 500
  }
}
```

**Respuesta Error**:
```json
{
  "exito": false,
  "mensaje": "Email o contraseña incorrectos"
}
```

---

### 3. **Abrir Juego**
**URL**: `https://blackjack-web-z4fm.onrender.com/?user_id=juan@email.com`

El juego carga automáticamente el saldo desde PostgreSQL.

---

## 🎨 Bloques de App Inventor

### Pantalla de Registro

```
cuando Boton_Registrar.Clic
  llamar Web1.PostText
    url: "https://blackjack-web-z4fm.onrender.com/api/registrar"
    text: crear objeto JSON con:
      - nombre: TextBox_Nombre.Texto
      - apellido: TextBox_Apellido.Texto
      - curp: TextBox_CURP.Texto
      - email: TextBox_Email.Texto
      - password: TextBox_Password.Texto

cuando Web1.GotText
  responseContent: responseContent
  
  establecer resultado a decodificar JSON responseContent
  
  si obtener propiedad(resultado, "exito") = verdadero entonces
    mostrar notificacion "Registro exitoso"
    abrir otra pantalla "PantallaLogin"
  sino
    mostrar notificacion obtener propiedad(resultado, "mensaje")
```

---

### Pantalla de Login

```
cuando Boton_Login.Clic
  llamar Web1.PostText
    url: "https://blackjack-web-z4fm.onrender.com/api/login_usuario"
    text: crear objeto JSON con:
      - email: TextBox_Email.Texto
      - password: TextBox_Password.Texto

cuando Web1.GotText
  responseContent: responseContent
  
  establecer resultado a decodificar JSON responseContent
  
  si obtener propiedad(resultado, "exito") = verdadero entonces
    // Guardar datos del usuario en TinyDB
    establecer global usuario a obtener propiedad(resultado, "usuario")
    establecer global user_email a obtener propiedad(global usuario, "email")
    establecer global user_nombre a obtener propiedad(global usuario, "nombre")
    establecer global user_saldo a obtener propiedad(global usuario, "saldo")
    
    llamar TinyDB1.GuardarValor
      etiqueta: "user_email"
      valorAGuardar: global user_email
    
    // Abrir pantalla del juego
    abrir otra pantalla "PantallaJuego"
  sino
    mostrar notificacion obtener propiedad(resultado, "mensaje")
```

---

### Pantalla del Juego (Blackjack)

```
cuando PantallaJuego.Inicializar
  // Recuperar email del usuario de TinyDB
  establecer global user_email a llamar TinyDB1.ObtenerValor
    etiqueta: "user_email"
    valorSiNoExiste: ""
  
  // Abrir el juego en WebViewer
  llamar VisorWeb1.irAUrl
    url: join("https://blackjack-web-z4fm.onrender.com/?user_id=", global user_email)
```

---

## 🔒 Seguridad

### Contraseñas
- Se encriptan con **SHA256** antes de guardar en la base de datos
- Nunca se almacenan en texto plano
- La verificación se hace comparando hashes

### Sesiones
- Se crean automáticamente al hacer login
- Duran 1 hora
- El WebViewer mantiene la sesión activa

---

## 📊 Flujo Completo

```
1. Usuario abre la app
   ↓
2. Pantalla de Login/Registro
   ↓
3. POST /api/registrar (si es nuevo)
   o
   POST /api/login_usuario (si ya existe)
   ↓
4. Guardar email en TinyDB
   ↓
5. Abrir WebViewer con ?user_id=email
   ↓
6. Juego carga saldo desde PostgreSQL
   ↓
7. Usuario juega
   ↓
8. Saldo se actualiza en PostgreSQL automáticamente
```

---

## ✅ Ventajas de Este Sistema

1. **Sin Firebase**: Todo en PostgreSQL (más simple)
2. **Autenticación Segura**: Contraseñas encriptadas
3. **Saldo Persistente**: Se guarda en la base de datos
4. **Sesiones Automáticas**: WebViewer maneja las cookies
5. **Escalable**: Fácil agregar más funcionalidades

---

## 🚀 Próximos Pasos

1. Diseñar las pantallas en App Inventor (Login, Registro, Juego)
2. Configurar los bloques según esta guía
3. Desplegar en Render con la variable `DATABASE_URL`
4. Probar el flujo completo

---

## 🛠️ Troubleshooting

**Problema**: "Email o contraseña incorrectos"
- Verifica que el usuario esté registrado
- Verifica que la contraseña sea correcta
- Verifica que el usuario esté activo en la BD

**Problema**: "Error de conexión a BD"
- Verifica que `DATABASE_URL` esté configurada en Render
- Verifica que la base de datos de Neon.tech esté activa

**Problema**: "El saldo no se actualiza"
- Verifica que el `user_id` en la URL sea el email correcto
- Verifica que el usuario tenga un registro en la tabla `Saldo`
