// ========================================================
// INTEGRACIÓN CON BASE DE DATOS - CARGA DESPUÉS DE APP.JS
// ========================================================

const API_URL_DB = window.location.origin;

// Sobrescribir balance inicial a 0 (se cargará desde BD)
bankValue = 0;

// Cargar saldo desde la base de datos
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // CLAVE: Envía cookie automáticamente
        });

        if (response.ok) {
            const data = await response.json();
            bankValue = data.saldo;
            updateBalance();
            console.log('✅ Saldo cargado desde BD:', bankValue);
        } else {
            console.log('⚠️ Sin autenticación, usando saldo por defecto');
            // Si no hay autenticación, mantener el saldo en 0 o valor por defecto
            bankValue = 1000; // Valor por defecto para testing sin login
            updateBalance();
        }
    } catch (error) {
        console.log('⚠️ Error cargando saldo:', error);
        bankValue = 1000; // Valor por defecto en caso de error
        updateBalance();
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
