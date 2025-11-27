from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import db_connect # <-- Importamos la conexión a la BD cambios
import psycopg2              # <-- Importamos para manejar errores de BD

# =========================
#  APP & STATIC / TEMPLATES
# =========================
app = FastAPI(title="Royal Crumbs")

# --- MARCA DE VERSIÓN PARA DESPLIEGUE ---
print("✅✅✅ INICIANDO APLICACIÓN - VERSIÓN MÁS RECIENTE ✅✅✅")

# --- CORRECCIÓN ---
# Se ajustan las rutas para que coincidan con la estructura real del proyecto.
# Los archivos estáticos están en la carpeta 'static' a nivel raíz.
# Las plantillas están en la carpeta 'templates' a nivel raíz.
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Helper para ahorrar líneas
def render(tpl: str, request: Request) -> HTMLResponse:
    return templates.TemplateResponse(tpl, {"request": request})

# =========================
#  RUTAS DE LÓGICA / API
# =========================
# --- CORRECCIÓN CRÍTICA DE IMPORTACIÓN ---
# Se importa directamente desde la carpeta 'api' para evitar ambigüedades
# con posibles archivos duplicados en la carpeta 'app'.
# CORRECCIÓN FINAL: Se importa el objeto 'router' desde el archivo 'api.auth'
# y se le da el alias 'auth_router' para que el resto del código funcione.
from api.auth import router as auth_router
from api.agente_soporte import router as agente_router
from api.support import router as support_router
from app.middleware.auth_agente import verificar_rol_agente_redirect

# =========================
#  RUTAS DE LÓGICA / API
# =========================
# CORRECCIÓN FINAL: `app.include_router` espera el objeto APIRouter directamente.
# Como `auth_router` ya es el router, eliminamos el `.router` extra.
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agente_router, tags=["Agente Soporte"])
app.include_router(support_router, tags=["Support"])
# app.include_router(user_router.router, prefix="/api/user", tags=["Usuarios"])
# ... (Puedes descomentar las otras rutas una vez que el login funcione)

# --- AÑADIDO: ENDPOINT PARA OBTENER DATOS DEL USUARIO ---
@app.get("/api/user/{user_id}")
async def get_user_data(user_id: int):
    """
    Esta ruta busca en la base de datos la información de un usuario
    por su ID y también su saldo, y los devuelve en un JSON.
    """
    print(f"🔹 API: Solicitud de datos para el usuario ID: {user_id}")
    conn = None
    cursor = None
    try:
        conn = db_connect.get_connection()
        if conn is None:
            return JSONResponse({"error": "Error de conexión a la base de datos"}, status_code=500)
        
        cursor = conn.cursor()
        # Consulta que une las tablas Usuario y Saldo para obtener todos los datos
        cursor.execute(
            """
            SELECT u.nombre, u.apellido, u.email, s.saldo_actual
            FROM Usuario u
            JOIN Saldo s ON u.id_usuario = s.id_usuario
            WHERE u.id_usuario = %s
            """,
            (user_id,)
        )
        user_data = cursor.fetchone()

        if not user_data:
            return JSONResponse({"error": "Usuario no encontrado"}, status_code=404)

        # Devolvemos los datos en un formato JSON claro
        return {"nombre": user_data[0], "apellido": user_data[1], "email": user_data[2], "saldo": user_data[3]}

    except Exception as e:
        print(f"🚨 API ERROR (get_user_data): {e}")
        return JSONResponse({"error": "Error interno del servidor"}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
#  PÚBLICO / AUTH
# =========================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):                  # pantalla de carga
    return render("loading.html", request)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render("login.html", request)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render("register.html", request)

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return render("forgot_password.html", request)

# Aliases hacia /home
@app.get("/inicio")
@app.get("/index")
async def redirect_home():
    return RedirectResponse(url="/home", status_code=302)

# =========================
#  HOME / JUEGOS
# =========================
@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    return render("home.html", request)

@app.get("/games", response_class=HTMLResponse)
async def games_page(request: Request):
    return render("games.html", request)

# =========================
#  SOPORTE (MENÚ + SUBSECCIONES)
# =========================
@app.get("/support", response_class=HTMLResponse)
async def support_root(request: Request):
    return render("support.html", request)

# Categorías/FAQ
@app.get("/support/cuenta", response_class=HTMLResponse)
async def support_account(request: Request):
    return render("support-cuenta.html", request)

@app.get("/support/cartera", response_class=HTMLResponse)
async def support_wallet(request: Request):
    return render("support-cartera.html", request)

@app.get("/support/juegos", response_class=HTMLResponse)
async def support_games(request: Request):
    return render("support-juegos.html", request)

@app.get("/support/BonosYPromociones", response_class=HTMLResponse)
async def support_promos(request: Request):
    return render("support-BonosYPromociones.html", request)

# Chat en vivo
@app.get("/support/chat", response_class=HTMLResponse)
async def support_chat_redirect():
    # por defecto manda al activo
    return RedirectResponse(url="/support/chat/active", status_code=302)

@app.get("/support/chat/active", response_class=HTMLResponse)
async def support_chat_active(request: Request):
    return render("support-chat-activo.html", request)

@app.get("/support/chat/new", response_class=HTMLResponse)
async def support_chat_new(request: Request):
    return render("support-chat-nuevo.html", request)

@app.get("/support/chat/history", response_class=HTMLResponse)
async def support_chat_history(request: Request):
    return render("support-chat-historial.html", request)

# Tickets
@app.get("/support/tickets/active", response_class=HTMLResponse)
async def tickets_activo(request: Request):
    return render("support-tickets-activo.html", request)

@app.get("/support/tickets/new", response_class=HTMLResponse)
async def tickets_nuevo(request: Request):
    return render("support-tickets-nuevo.html", request)

@app.get("/support/tickets/history", response_class=HTMLResponse)
async def tickets_historial(request: Request):
    return render("support-tickets-historial.html", request)

# Legal & info
@app.get("/support/terminos", response_class=HTMLResponse)
async def support_terminos(request: Request):
    return render("support-terminos.html", request)

@app.get("/support/privacidad", response_class=HTMLResponse)
async def support_privacidad(request: Request):
    return render("support-privacidad.html", request)

@app.get("/support/juego-responsable", response_class=HTMLResponse)
async def support_juego_responsable(request: Request):
    return render("support-juego-responsable.html", request)

@app.get("/support/sobre-nosotros", response_class=HTMLResponse)
async def support_sobre_nosotros(request: Request):
    return render("support-sobre-nosotros.html", request)

# =========================
#  MI CUENTA (CONFIG / BONOS)
# =========================
@app.get("/account", response_class=HTMLResponse)
async def account_root(request: Request):
    # si quieres una portada de cuenta, cámbialo por otra plantilla
    return render("account.html", request)

@app.get("/account/configuracion", response_class=HTMLResponse)
async def account_config(request: Request):
    return render("account-configuracion.html", request)

@app.get("/account/metodos", response_class=HTMLResponse)
async def account_metodos(request: Request):
    return render("account-metodos.html", request)

@app.get("/account/tarjeta", response_class=HTMLResponse)
async def account_tarjeta(request: Request):
    return render("account-tarjeta.html", request)

@app.get("/account/bancaria", response_class=HTMLResponse)
async def account_bancaria(request: Request):
    return render("account-bancaria.html", request)

@app.get("/account/bonos", response_class=HTMLResponse)
async def account_bonos(request: Request):
    return render("account-bonos.html", request)

@app.get("/account/bonos-activos", response_class=HTMLResponse)
async def bonos_activos(request: Request):
    return render("account-bonos-activos.html", request)

@app.get("/account/bonos-historial", response_class=HTMLResponse)
async def bonos_historial(request: Request):
    return render("account-bonos-historial.html", request)

# =========================
#  CARTERA (DEP/RET/HIST/BALANCE)
# =========================
@app.get("/account/cartera", response_class=HTMLResponse)
async def account_cartera(request: Request):
    return render("account-cartera.html", request)

# Depósitos
@app.get("/account/cartera/depositos", response_class=HTMLResponse)
async def cartera_depositos(request: Request):
    return render("account-cartera-depositos.html", request)

@app.get("/account/cartera/depositos/tarjeta", response_class=HTMLResponse)
async def deposito_tarjeta(request: Request):
    return render("account-cartera-deposito-tarjeta.html", request)

@app.get("/account/cartera/depositos/transferencia", response_class=HTMLResponse)
async def deposito_transferencia(request: Request):
    return render("account-cartera-deposito-transferencia.html", request)

# Retiros
@app.get("/account/cartera/retiros", response_class=HTMLResponse)
async def cartera_retiros(request: Request):
    return render("account-cartera-retiros.html", request)

@app.get("/account/cartera/retiros/tarjeta", response_class=HTMLResponse)
async def retiros_tarjeta(request: Request):
    return render("account-cartera-retiros-tarjeta.html", request)

@app.get("/account/cartera/retiros/transferencia", response_class=HTMLResponse)
async def retiros_transferencia(request: Request):
    return render("account-cartera-retiros-transferencia.html", request)

# Historiales y balance
@app.get("/account/cartera/historial", response_class=HTMLResponse)
async def cartera_historial_menu(request: Request):
    return render("account-cartera-historial.html", request)

@app.get("/account/cartera/historial-transacciones", response_class=HTMLResponse)
async def historial_transacciones(request: Request):
    return render("account-cartera-historial-transacciones.html", request)

@app.get("/account/cartera/historial-juegos", response_class=HTMLResponse)
async def historial_juegos(request: Request):
    return render("account-cartera-historial-juegos.html", request)

@app.get("/account/cartera/balance", response_class=HTMLResponse)
async def cartera_balance(request: Request):
    return render("account-cartera-balance.html", request)


# =========================
#  ADMINISTRACIÓN
# =========================
@app.get("/admin", response_class=HTMLResponse)
async def admin_menu(request: Request):
    return render("admin.html", request)

# Información general (dashboard)
@app.get("/admin/info-general", response_class=HTMLResponse)
async def admin_info_general(request: Request):
    return render("admin-info-general.html", request)

# Gestión de usuarios (menú)
@app.get("/admin/gestion-usuarios", response_class=HTMLResponse)
async def admin_gestion_usuarios(request: Request):
    return render("admin-gestion-usuarios.html", request)

# Listado y perfiles
@app.get("/admin/usuarios", response_class=HTMLResponse)
async def admin_usuarios(request: Request):
    return render("admin-usuarios.html", request)

@app.get("/admin/administradores", response_class=HTMLResponse)
async def admin_administradores(request: Request):
    return render("admin-administradores.html", request)

@app.get("/admin/usuarios/perfil", response_class=HTMLResponse)
async def admin_usuario_perfil(request: Request):
    return render("admin-usuario-perfil.html", request)

@app.get("/admin/administradores/perfil", response_class=HTMLResponse)
async def admin_administrador_perfil(request: Request):
    return render("admin-administrador-perfil.html", request)

# Gestión de juegos
@app.get("/admin/juegos", response_class=HTMLResponse)
async def admin_juegos(request: Request):
    return render("admin-juegos.html", request)

# Configuración del sistema
@app.get("/admin/configuracion", response_class=HTMLResponse)
async def admin_configuracion(request: Request):
    return render("admin-configuracion.html", request)

@app.get("/admin/configuracion/bloquear-ip", response_class=HTMLResponse)
async def admin_bloquear_ip(request: Request):
    return render("admin-configuracion-bloquear-ip.html", request)

@app.get("/admin/configuracion/lista-blanca", response_class=HTMLResponse)
async def admin_lista_blanca(request: Request):
    return render("admin-configuracion-lista-blanca.html", request)

# Promociones
@app.get("/admin/promociones", response_class=HTMLResponse)
async def admin_promociones(request: Request):
    return render("admin-promociones.html", request)

# =========================
#  PANEL DE AGENTE DE SOPORTE
# =========================
@app.get("/agente", response_class=HTMLResponse)
async def agente_menu(request: Request):
    # Verificar que el usuario tiene rol de Soporte
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente.html", request)

# Dashboard del agente
@app.get("/agente/dashboard", response_class=HTMLResponse)
async def agente_dashboard(request: Request):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-dashboard.html", request)

# Gestión de tickets
@app.get("/agente/tickets", response_class=HTMLResponse)
async def agente_tickets(request: Request):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-tickets.html", request)

@app.get("/agente/mis-tickets", response_class=HTMLResponse)
async def agente_mis_tickets(request: Request):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-mis-tickets.html", request)

@app.get("/agente/ticket/{id_ticket}", response_class=HTMLResponse)
async def agente_ticket_detalle(request: Request, id_ticket: int):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-ticket-detalle.html", request)

# Gestión de chats
@app.get("/agente/chats", response_class=HTMLResponse)
async def agente_chats(request: Request):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-chats.html", request)

@app.get("/agente/mis-chats", response_class=HTMLResponse)
async def agente_mis_chats(request: Request):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-mis-chats.html", request)

@app.get("/agente/chat/{id_chat}", response_class=HTMLResponse)
async def agente_chat_activo(request: Request, id_chat: int):
    redirect = await verificar_rol_agente_redirect(request)
    if redirect:
        return redirect
    return render("agente-chat-activo.html", request)
