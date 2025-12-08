// Integración con Base de Datos - Royal Crumbs
// Este archivo se carga DESPUÉS de app.js y carga el saldo inicial

const API_URL_DB = window.location.origin;

// Sobrescribir balance inicial a 0
bankValue = 0;

// Cargar saldo desde la base de datos usando cookies de sesión
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // Envía cookies de sesión automáticamente
        });

        if (response.ok) {
            const data = await response.json();
            bankValue = data.saldo;
            updateBalance();
            console.log('✅ Saldo cargado desde BD:', bankValue);
        } else {
            console.log('⚠️ Sin autenticación, redirigiendo a login...');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('❌ Error cargando saldo:', error);
        window.location.href = '/login';
    }
}

// Función para actualizar el display del balance
function updateBalance() {
    const bankSpan = document.getElementById('bankSpan');
    if (bankSpan) {
        bankSpan.innerText = '' + bankValue.toLocaleString("en-GB") + '';
    }
}

// Cargar saldo al iniciar la página
loadBalanceFromDB();
