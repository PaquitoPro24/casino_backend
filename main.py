from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import db_connect # <-- Importamos la conexión a la BD cambios
import psycopg2              # <-- Importamos para manejar errores de BD
from psycopg2.extras import RealDictCursor # <-- Para queries con diccionarios

# --- NUEVOS IMPORTS PARA AUDITOR ---
from pydantic import BaseModel
from typing import Dict, Any, List
import datetime # <-- ¡AÑADIMOS ESTE IMPORT!
from api.i18n import load_translations, trans # <-- Importar i18n

# =========================
#  APP & STATIC / TEMPLATES
# =========================
from fastapi.middleware.cors import CORSMiddleware # Importar CORS

app = FastAPI(title="Royal Crumbs")

# Configurar CORS para permitir que los juegos externos (tragamonedas-web.onrender.com, etc)
# consulten este backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por dominios específicos de los juegos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MARCA DE VERSIÓN PARA DESPLIEGUE ---
print("✅✅✅ INICIANDO APLICACIÓN - VERSIÓN MÁS RECIENTE ✅✅✅")

# --- CORRECCIÓN ---
# Se ajustan las rutas para que coincidan con la estructura real del proyecto.
# Los archivos estáticos están en la carpeta 'static' a nivel raíz.
# Las plantillas están en la carpeta 'templates' a nivel raíz.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/juegos", StaticFiles(directory="juegos"), name="juegos") # <-- Montar juegos locales
templates = Jinja2Templates(directory="templates")

# --- i18n SETUP ---
load_translations("locales")
templates.env.globals["trans"] = trans


# --- SERVIR SERVICE WORKER DESDE LA RAÍZ ---
# Esto es necesario para que el SW tenga alcance (scope) sobre toda la app, no solo /static/
from fastapi.responses import FileResponse
@app.api_route("/sw.js", methods=["GET", "HEAD"], include_in_schema=False)
async def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript")

@app.api_route("/manifest.json", methods=["GET", "HEAD"], include_in_schema=False)
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

@app.api_route("/.well-known/assetlinks.json", methods=["GET", "HEAD"], include_in_schema=False)
async def assetlinks():
    return FileResponse("static/assetlinks.json", media_type="application/json")

# Helper para ahorrar líneas
def render(tpl: str, request: Request, context: dict = None) -> HTMLResponse:
    ctx = {"request": request}
    if context:
        ctx.update(context)
    return templates.TemplateResponse(tpl, ctx)

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
from api.admin import router as admin_router
from api.user import router as user_router_api
from api.wallet import router as wallet_router
from api.bonos import router as bonos_router
from api.game_endpoints import router as game_router # <-- Nuevo Router de Juegos
from api.blackjack_endpoints import router as blackjack_router # <-- Router de Blackjack
from api.auditor import router as auditor_router # <-- Router de Auditor


from app.middleware.auth_agente import verificar_rol_agente_redirect

# =========================
#  RUTAS DE LÓGICA / API
# =========================
# Montamos todos los routers de API
app.include_router(auth_router)
app.include_router(agente_router)
app.include_router(support_router)
app.include_router(admin_router)
app.include_router(user_router_api)
app.include_router(wallet_router)
app.include_router(bonos_router)
app.include_router(game_router)
app.include_router(blackjack_router)
app.include_router(auditor_router)

# =========================
#  PÚBLICO / AUTH
# =========================
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def root(request: Request):                  # pantalla de carga
    return render("loading.html", request)

@app.get("/offline", response_class=HTMLResponse)
async def offline(request: Request):
    return render("offline.html", request)

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

@app.get("/play/{game_id}", response_class=HTMLResponse)
async def play_game(request: Request, game_id: str):
    # 1. Obtener User ID de la cookie
    user_id = request.cookies.get("userId")
    if not user_id:
        return RedirectResponse(url="/login")

    # 2. Mapeo de juegos LOCALES
    games_map = {
        "tragamonedas": {"url": "/juegos/tragamonedas-web/index.html", "name": "Tragamonedas"},
        "ruleta": {"url": "/juegos/ruleta-web/index.html", "name": "Ruleta"},
        "blackjack": {"url": "/juegos/blackjack-web/index.html", "name": "Blackjack"},
    }
    game = games_map.get(game_id)
    if not game:
        return RedirectResponse(url="/games")
    
    # 3. Construir URL con el ID y la URL del Backend
    # Pasamos 'api_url' para que el juego sepa dónde consultar el saldo (Cross-Origin)
    base_url = str(request.base_url).rstrip('/')
    # FORZAR HTTPS: Render termina SSL en el load balancer, así que base_url puede ser http.
    # Los juegos están en https, así que necesitamos que la API también se llame por https para evitar Mixed Content.
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://", 1)
        
    final_url = f"{game['url']}?user_id={user_id}&api_url={base_url}"
    
    return render("play_game.html", request, {"game_url": final_url, "game_name": game["name"]})



# =========================
#  SOPORTE (MENÚ + SUBSECCIONES)
# =========================
@app.get("/api/saldo")
async def api_get_balance_cookie(request: Request):
    """Endpoint para obtener saldo vía cookie (para juegos locales)."""
    user_id = request.cookies.get("userId")
    if not user_id:
        return JSONResponse({"error": "No autenticado"}, status_code=401)
    
    conn = None
    try:
        conn = db_connect.get_connection()
        if conn is None: return JSONResponse({"error": "Error de conexión"}, status_code=500)
        
        cursor = conn.cursor()
        cursor.execute("SELECT saldo_actual FROM Saldo WHERE id_usuario = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        
        saldo = float(result[0]) if result else 0.0
        return JSONResponse({"saldo": saldo})
            
    except Exception as e:
        print(f"🚨 API ERROR (Saldo): {e}")
        return JSONResponse({"error": "Error interno"}, status_code=500)
    finally:
        if conn: conn.close()

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
#  PANEL DE AUDITOR
# =========================
@app.get("/auditor", response_class=HTMLResponse)
async def auditor_menu(request: Request):
    return render("auditor.html", request)

@app.get("/auditor/realizar", response_class=HTMLResponse)
async def auditor_realizar(request: Request):
    return render("auditor-realizar.html", request)

@app.get("/auditor/historial", response_class=HTMLResponse)
async def auditor_historial(request: Request):
    return render("auditor-historial.html", request)

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

# =========================
#  AUDITOR (PANEL + REALIZAR + HISTORIAL)
# =========================
@app.get("/auditor", response_class=HTMLResponse)
async def auditor_panel(request: Request):
    """Panel principal del auditor"""
    return render("auditor.html", request)

@app.get("/auditor/realizar", response_class=HTMLResponse)
async def auditor_realizar(request: Request):
    """Formulario para realizar nueva auditoría"""
    return render("auditor-realizar.html", request)

@app.get("/auditor/historial", response_class=HTMLResponse)
async def auditor_historial_page(request: Request):
    """Página de historial de auditorías"""
    return render("auditor-historial.html", request)

@app.get("/auditor/ver_pdf/{id_auditoria}", response_class=HTMLResponse)
async def auditor_ver_pdf(request: Request, id_auditoria: int):
    """Visor de PDF de auditoría"""
    return render("auditor-ver-pdf.html", request, {"id_auditoria": id_auditoria})