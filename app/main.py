from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# =========================
#  APP & STATIC / TEMPLATES
# =========================
app = FastAPI(title="Royal Crumbs")

# Ajusta estas rutas si tu estructura cambia
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Helper para ahorrar líneas
def render(tpl: str, request: Request) -> HTMLResponse:
    return templates.TemplateResponse(tpl, {"request": request})

# =========================
#  RUTAS DE LÓGICA / API
# =========================
from app.routers import (
    auth_router,
    user_router,
    transacciones_router,
    juegos_router,
    soporte_router,
    bonos_router
)

# =========================
#  RUTAS DE LÓGICA / API
# =========================
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_router.router, prefix="/api/user", tags=["Usuarios"])
app.include_router(transacciones_router.router, prefix="/api/transacciones", tags=["Transacciones"])
app.include_router(juegos_router.router, prefix="/api/juegos", tags=["Juegos"])
app.include_router(soporte_router.router, prefix="/api/soporte", tags=["Soporte"])
app.include_router(bonos_router.router, prefix="/api/bonos", tags=["Bonos"])


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
