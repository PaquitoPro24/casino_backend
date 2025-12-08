// db-integration.js - Carga de saldo desde PostgreSQL - Royal Crumbs
// Este archivo se carga DESPUÉS de app.js

const API_URL_DB = window.location.origin;

// Cargar saldo desde la base de datos usando cookies de sesión
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // Envía cookies de sesión automáticamente
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Saldo cargado desde BD:', data.saldo);
            // El saldo se sincroniza automáticamente a través de /api/state
        } else {
            console.log('⚠️ Sin autenticación, redirigiendo a login...');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('❌ Error cargando saldo:', error);
        window.location.href = '/login';
    }
}

// Cargar saldo al iniciar
loadBalanceFromDB();
