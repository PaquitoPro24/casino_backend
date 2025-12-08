// Integración con Base de Datos
// Este archivo se carga DESPUÉS de app.js y agrega funcionalidad de BD

const API_URL_DB = window.location.origin;

// Sobrescribir balance inicial a 0
balance = 0;

// Función para cargar saldo desde BD
async function loadBalanceFromDB() {
    try {
        const response = await fetch(`${API_URL_DB}/api/saldo`, {
            credentials: 'include'  // Envía cookie de App Inventor
        });

        if (response.ok) {
            const data = await response.json();
            balance = data.saldo;
            updateBalance();
            console.log('✅ Saldo cargado desde BD:', balance);
        } else {
            console.log('⚠️ Sin autenticación, usando saldo por defecto');
        }
    } catch (error) {
        console.log('⚠️ Error cargando saldo:', error);
    }
}

// NOTA: La lógica de actualización de saldo está en app.js > spinOnce()
// que ya llama al endpoint /spin y actualiza correctamente el balance
// tanto para victorias como para pérdidas.

// Cargar saldo al iniciar
loadBalanceFromDB();

// === NUEVO: Integración por ID de usuario en URL ===
const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('user_id');
const backendUrl = urlParams.get('api_url');

if (userId) {
    let fetchUrl;
    if (backendUrl) {
        console.log("Conectando al backend:", backendUrl);
        // Usamos la URL absoluta del backend que recibimos
        fetchUrl = `${backendUrl}/api/user/${userId}`;
    } else {
        // Fallback: usar ruta relativa si no hay api_url
        fetchUrl = `/api/user/${userId}`;
    }

    fetch(fetchUrl)
        .then(response => response.json())
        .then(data => {
            if (data.saldo !== undefined) {
                console.log("Saldo recibido:", data.saldo);
                // Actualiza la variable de saldo del juego y la UI
                balance = data.saldo;
                updateBalance();
            }
        })
        .catch(err => console.error("Error conectando:", err));
} else {
    // No interfiere con la lógica de App Inventor si no hay user_id
    console.log("No se detectó parameter 'user_id' en la URL, continuando con flujo normal.");
}
