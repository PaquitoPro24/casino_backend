# 🚀 CONFIGURACIÓN RENDER - PASO A PASO

## ⚠️ ACCIÓN REQUERIDA: Cambiar Start Command

Tu código está 100% correcto, pero **DEBES cambiar una configuración en el dashboard de Render**.

---

## 📍 PASOS (2 minutos)

### 1️⃣ Ir a Settings
1. Abre [render.com](https://render.com)
2. Ve a tu Web Service "blackjack-web"
3. Click en **"Settings"** (menú izquierdo)

### 2️⃣ Cambiar Start Command
1. Scroll hasta la sección **"Build & Deploy"**
2. Busca el campo **"Start Command"**
3. **Borra** lo que dice (probablemente `gunicorn app:app`)
4. **Escribe** esto:
   ```
   uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
5. Click en **"Save Changes"**

### 3️⃣ Esperar Deploy
- Render redesplegará automáticamente
- Espera 2-3 minutos
- Verás el status cambiar a "Live" 🟢

---

## ✅ CONFIGURACIÓN COMPLETA

Cuando termines el paso anterior, tu configuración debe ser:

### Build Command
```
pip install -r requirements.txt
```

### Start Command  
```
uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Environment
- Python 3

### Variables de Entorno (Environment)
- `DATABASE_URL` → *(Ya configurada automáticamente)*
- `JWT_SECRET` → Genera una con este comando en tu terminal local:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  Copia el resultado y agrégalo como variable de entorno en Render.

---

## 🎯 VERIFICAR QUE FUNCIONÓ

Después del deploy verás en los logs:

```
✅ Conexión exitosa a PostgreSQL
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:10000
```

**Probar la app:**
```
https://TU-APP.onrender.com/?user_email=test@example.com
```

---

## 🔧 Si aún falla después de cambiar el Start Command

1. **Verifica que las variables de entorno estén configuradas:**
   - `DATABASE_URL` debe estar presente
   - `JWT_SECRET` debe estar configurado

2. **Fuerza un nuevo deploy:**
   - Settings → Manual Deploy → "Deploy latest commit"

3. **Revisa los logs:**
   - Ve a "Logs" en el menú
   - Busca errores después de que diga "Started server process"

---

## 📝 RESUMEN

✅ Tu código está correcto (Ya commiteado)
✅ `Procfile` tiene el comando correcto
✅ `requirements.txt` tiene todas las dependencias

❌ **LO ÚNICO QUE FALTA**: Cambiar el Start Command en el dashboard de Render

**No puedo hacer esto por ti porque es configuración en la web de Render, pero solo toma 30 segundos!** 🚀
