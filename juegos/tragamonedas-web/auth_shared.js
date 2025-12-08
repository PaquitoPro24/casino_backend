// Shared Authentication Logic

// Usar el origen actual del navegador (funciona local y en producción)
const API_URL = window.location.origin;

// FUNCIÓN HELPER PARA OBTENER TOKEN
function getToken() {
  return localStorage.getItem('token');
}

// FUNCIÓN PARA CERRAR SESIÓN
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  // Redirigir al login si no estamos en la página de login
  if (!window.location.pathname.includes('login.html')) {
    window.location.href = '/static/login.html';
  }
}

// Verificar autenticación al cargar la página
function checkAuth() {
  const token = getToken();
  if (!token && !window.location.pathname.includes('login.html')) {
    // Si no hay token, NO redirigir. Asumir modo "Invitado".
    console.log("Modo Invitado: No hay sesión activa.");
    return;
  }
}

// Ejecutar verificación
checkAuth();
