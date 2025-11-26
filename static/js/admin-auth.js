/**
 * Utilidad centralizada para verificación de autenticación en páginas de administrador
 * Este archivo debe ser incluido en todas las páginas que requieran autenticación de admin
 */

/**
 * Verifica si el usuario tiene permisos de administrador o auditor
 * @param {boolean} showAlert - Si debe mostrar una alerta antes de redirigir
 * @param {boolean} debug - Si debe mostrar información de debug en la consola
 * @returns {boolean} - true si el usuario está autenticado, false si no
 */
function checkAdminAuth(showAlert = true, debug = false) {
  // Obtener valores de localStorage
  const userId = localStorage.getItem("user_id");
  const userRole = localStorage.getItem("user_role");
  
  // Debug info
  if (debug) {
    console.log("=== AUTH DEBUG ===");
    console.log("User ID:", userId);
    console.log("User Role (raw):", `"${userRole}"`);
    console.log("User Role length:", userRole ? userRole.length : 0);
  }
  
  // Verificar si existe el ID de usuario
  if (!userId) {
    if (debug) console.log("❌ No user_id found in localStorage");
    if (showAlert) alert("Sesión no encontrada. Por favor, inicia sesión.");
    window.location.href = "/login";
    return false;
  }
  
  // Verificar si existe el rol
  if (!userRole) {
    if (debug) console.log("❌ No user_role found in localStorage");
    if (showAlert) alert("Rol de usuario no encontrado. Por favor, inicia sesión nuevamente.");
    localStorage.clear(); // Limpiar localStorage corrupto
    window.location.href = "/login";
    return false;
  }
  
  // Normalizar el rol (lowercase y trim)
  const normalizedRole = userRole.toLowerCase().trim();
  
  if (debug) {
    console.log("User Role (normalized):", `"${normalizedRole}"`);
    console.log("Is Administrador?", normalizedRole === 'administrador');
    console.log("Is Auditor?", normalizedRole === 'auditor');
  }
  
  // Verificar si el rol es administrador o auditor
  if (normalizedRole !== 'administrador' && normalizedRole !== 'auditor') {
    if (debug) console.log("❌ User role is not admin or auditor:", normalizedRole);
    if (showAlert) alert("Acceso denegado. No tienes permisos de administrador.");
    window.location.href = "/login";
    return false;
  }
  
  if (debug) console.log("✅ Authentication successful");
  return true;
}

/**
 * Versión simplificada sin alertas (para páginas que manejan el error de otra forma)
 */
function checkAdminAuthSilent() {
  return checkAdminAuth(false, false);
}

/**
 * Versión con debug activado (útil para troubleshooting)
 */
function checkAdminAuthDebug() {
  return checkAdminAuth(true, true);
}
