# 🔧 Solución al Error "uvicorn: command not found" en Render

## 📋 Archivos Necesarios

Asegúrate de tener estos archivos en tu repositorio:

### ✅ runtime.txt (NUEVO - Ya creado)
```
python-3.11.0
```

### ✅ requirements.txt
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
```

### ✅ Procfile (Opcional en Render)
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

---

## 🚀 Configuración EXACTA en Render Dashboard

Cuando crees o edites tu Web Service en Render, usa **EXACTAMENTE** esta configuración:

### Configuración del Servicio

| Campo | Valor EXACTO |
|-------|--------------|
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |

> [!IMPORTANT]
> El **Build Command** es CRUCIAL. Sin esto, las dependencias no se instalan.

---

## 📸 Pasos Detallados

### Opción 1: Si ya creaste el servicio

1. Ve a tu Web Service en el dashboard de Render
2. Click en **"Settings"** en el menú izquierdo
3. Busca la sección **"Build & Deploy"**
4. Verifica/cambia estos campos:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Click en **"Save Changes"**
6. Ve a la pestaña **"Manual Deploy"**
7. Click en **"Deploy latest commit"**

### Opción 2: Si vas a crear un nuevo servicio

1. Click en **"New +"** → **"Web Service"**
2. Conecta tu repositorio
3. En la configuración usa:
   - **Name:** `tragamonedas-web`
   - **Region:** Oregon (USA) o la más cercana
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. Click **"Create Web Service"**

---

## 🔄 Actualizar el Repositorio

Primero, asegúrate de subir el nuevo archivo `runtime.txt`:

```bash
# Agregar el nuevo archivo
git add runtime.txt

# Hacer commit
git commit -m "Add runtime.txt for Render"

# Subir a GitHub
git push origin main
```

Render detectará automáticamente el cambio y redesplegará.

---

## 🐛 Verificar los Logs

Después de desplegar, verifica los logs en Render:

1. Ve a tu Web Service
2. Click en **"Logs"**
3. Deberías ver algo como:

```
==> Downloading Python version 3.11.0
==> Installing dependencies from requirements.txt
Collecting fastapi>=0.104.0
Collecting uvicorn[standard]>=0.24.0
...
Successfully installed fastapi-... uvicorn-...
==> Running 'uvicorn app:app --host 0.0.0.0 --port 10000'
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## ✅ Checklist de Verificación

- [ ] `runtime.txt` existe y contiene `python-3.11.0`
- [ ] `requirements.txt` está correcto
- [ ] Build Command en Render: `pip install -r requirements.txt`
- [ ] Start Command en Render: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- [ ] Cambios subidos a GitHub con `git push`
- [ ] Redesplegar en Render (automático o manual)

---

## 💡 Nota Importante

> [!WARNING]
> NO uses el `Procfile` en la configuración del Start Command en Render.
> El Procfile es para Heroku. En Render debes usar directamente el comando en el campo "Start Command".

El comando correcto es:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

**NO** uses:
- ❌ `web: uvicorn app:app --host 0.0.0.0 --port $PORT`
- ❌ `python app.py`
