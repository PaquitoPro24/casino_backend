// db-integration.js - Carga de saldo desde PostgreSQL
// Este archivo se carga DESPUÉS de app.js

const API_URL_DB = window.location.origin;

// Cargar saldo desde la base de datos
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // CLAVE: Envía cookie automáticamente
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Saldo cargado desde BD:', data.saldo);
            console.log('✅ Usuario:', data.usuario.nombre, data.usuario.apellido);

            // El saldo ya se sincroniza automáticamente a través de /api/state
            // Este endpoint es solo para verificar la autenticación
        } else {
            console.log('⚠️ Sin autenticación, verificar cookie access_token');
        }
    } catch (error) {
        console.log('⚠️ Error cargando saldo:', error);
    }
}

// Cargar saldo al iniciar la página
loadBalanceFromDB();
