// Integración con Base de Datos - Royal Crumbs
// Este archivo se carga DESPUÉS de app.js y carga el saldo inicial

const API_URL_DB = window.location.origin;

// Sobrescribir balance inicial a 0
balance = 0;

// Función para cargar saldo desde BD usando cookies de sesión
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // Envía cookies de sesión automáticamente
        });

        if (response.ok) {
            const data = await response.json();
            balance = data.saldo;
            updateBalance();
            console.log('✅ Saldo cargado desde BD:', balance);
        } else {
            console.log('⚠️ Sin autenticación, redirigiendo a login...');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('❌ Error cargando saldo:', error);
        window.location.href = '/login';
    }
}

// NOTA: La lógica de actualización de saldo está en app.js > spinOnce()
// que ya llama al endpoint /spin y actualiza correctamente el balance

// Cargar saldo al iniciar
loadBalanceFromDB();
