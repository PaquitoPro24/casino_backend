// Usar el origen actual del navegador (funciona local y en producción)
const API_URL = window.location.origin;

let balance = 0;  // Se cargará desde la API
let autoSpin = false;
let spinning = false;

// FUNCIÓN HELPER PARA OBTENER TOKEN
function getToken() {
  return localStorage.getItem('token');
}

// FUNCIÓN PARA CERRAR SESIÓN
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/static/login.html';
}

const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");
const betInput = document.getElementById("bet");
const autoBtn = document.getElementById("autoBtn");
const balanceEl = document.getElementById("balance");
const leverContainer = document.getElementById("leverContainer");
const leverArm = document.getElementById("leverArm");

// Símbolos disponibles en el frontend
const SYMBOLS = ["❔", "🍒", "🍋", "🍇", "⭐", "7️⃣", "🔔"];

// Crear las 3 columnas (rodillos)
const reels = [];
for (let i = 0; i < 3; i++) {
  const reelContainer = document.createElement("div");
  reelContainer.className = "reel";

  // Cada rodillo tendrá 3 celdas visibles
  for (let j = 0; j < 3; j++) {
    const cell = document.createElement("div");
    cell.className = "cell";
    const symbolDiv = document.createElement("div");
    symbolDiv.className = "symbol";
    symbolDiv.textContent = "❔";
    cell.appendChild(symbolDiv);
    reelContainer.appendChild(cell);
  }
  gridEl.appendChild(reelContainer);
  reels.push(reelContainer);
}

function updateBalance() {
  balanceEl.textContent = "$" + balance.toFixed(2);
}

function setStatus(text) {
  statusEl.textContent = text;
}

// CARGAR SALDO DESDE LA API AL INICIAR
async function loadBalance() {
  console.log('🔄 Cargando saldo desde la API...');
  try {
    const token = getToken();
    console.log('Token encontrado:', token ? 'Sí' : 'No');

    const response = await fetch(`${API_URL}/api/saldo`, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'  // Importante para cookies
    });

    console.log('Respuesta API saldo status:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('Datos recibidos:', data);
      balance = data.saldo;
      updateBalance();

      // Mostrar nombre del usuario
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userNameEl = document.getElementById('userName');
      if (userNameEl && user.nombre) {
        userNameEl.textContent = `${user.nombre} ${user.apellido}`;
      }

      console.log('✅ Saldo cargado correctamente:', balance);
    } else if (response.status === 401) {
      console.warn('⚠️ Token inválido o expirado, redirigiendo a login...');
      // Token inválido, redirigir a login
      logout();
    } else {
      console.error('❌ Error al cargar saldo, status:', response.status);
    }
  } catch (error) {
    console.error('❌ Error al cargar saldo:', error);
    setStatus('❌ Error al cargar saldo');
  }
}

// Animación de la palanca
function pullLever() {
  if (spinning) return;

  // Sonido de palanca
  if (typeof soundManager !== 'undefined') {
    soundManager.playLeverSound();
  }

  leverArm.classList.add("pulled");

  setTimeout(() => {
    leverArm.classList.remove("pulled");
    spinOnce();
  }, 300);
}

// Event listener para la palanca
leverContainer.addEventListener("click", pullLever);

// === FUNCIONES DE EFECTOS VISUALES ===

// Crear confeti
function createConfetti(count) {
  const colors = ['#ab925c', '#FF6347', '#00FF00', '#1E90FF', '#FF69B4', '#FFA500'];

  for (let i = 0; i < count; i++) {
    setTimeout(() => {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = Math.random() * 100 + 'vw';
      confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
      confetti.style.animationDelay = (Math.random() * 0.5) + 's';
      document.body.appendChild(confetti);

      setTimeout(() => confetti.remove(), 4000);
    }, i * 30);
  }
}

// Crear flash dorado
function createFlash() {
  const flash = document.createElement('div');
  flash.className = 'golden-flash';
  document.body.appendChild(flash);
  setTimeout(() => flash.remove(), 600);
}

// Crear overlay de celebración
function createCelebrationOverlay() {
  const overlay = document.createElement('div');
  overlay.className = 'celebration-overlay';
  document.body.appendChild(overlay);
  setTimeout(() => overlay.remove(), 800);
}

// Crear texto de gran victoria
function createBigWinText(text) {
  const bigWin = document.createElement('div');
  bigWin.className = 'big-win-text';
  bigWin.textContent = text;
  document.body.appendChild(bigWin);
  setTimeout(() => bigWin.remove(), 2000);
}

// Crear overlay de pérdida
function createLossOverlay() {
  const overlay = document.createElement('div');
  overlay.className = 'loss-overlay';
  document.body.appendChild(overlay);
  setTimeout(() => overlay.remove(), 800);
}

// Crear texto de pérdida
function createLossText() {
  const lossText = document.createElement('div');
  lossText.className = 'loss-text';
  lossText.textContent = '😞';
  document.body.appendChild(lossText);
  setTimeout(() => lossText.remove(), 1500);
}

async function spinOnce() {
  if (spinning) return;

  const bet = parseInt(betInput.value);

  if (bet > balance) {
    setStatus("💸 Saldo insuficiente");
    return;
  }

  spinning = true;
  setStatus("🎰 Girando...");

  // Temporalmente descontar para mostrar animación
  const balanceAnterior = balance;
  balance -= bet;
  updateBalance();

  // Sonido de giro
  if (typeof soundManager !== 'undefined') {
    soundManager.playSpinSound();
  }

  // Agregar clase spinning para activar animación de blur
  reels.forEach(reel => reel.classList.add("spinning"));

  // Array para almacenar los resultados de cada rodillo
  const finalGrid = [[], [], []];

  // Iniciar animación de giro - CADA RODILLO OBTIENE SU RESULTADO INDEPENDIENTEMENTE
  const spinPromises = reels.map((reel, reelIndex) => {
    return new Promise((resolve) => {
      const symbols = reel.querySelectorAll('.symbol');
      let spinCount = 0;
      const maxSpins = 20 + (reelIndex * 10);

      const animationInterval = setInterval(() => {
        symbols.forEach(s => {
          s.textContent = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
        });
        spinCount++;

        if (spinCount >= maxSpins) {
          clearInterval(animationInterval);

          // Obtener resultado para ESTE rodillo específico del servidor
          fetch(`${API_URL}/reel`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reel_index: reelIndex })
          })
            .then(res => res.json())
            .then(data => {
              // Guardar resultado en el grid
              finalGrid[reelIndex] = data.symbols;

              // Mostrar el resultado final de ESTE rodillo
              symbols.forEach((s, symbolIndex) => {
                s.textContent = data.symbols[symbolIndex];
              });

              reel.classList.remove("spinning");

              // Sonido de detención del rodillo
              if (typeof soundManager !== 'undefined') {
                soundManager.playReelStopSound();
              }

              resolve();
            })
            .catch(error => {
              console.error("Error al obtener rodillo:", error);
              // En caso de error, usar símbolos aleatorios
              const fallbackSymbols = [
                SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
                SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
                SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)]
              ];
              finalGrid[reelIndex] = fallbackSymbols;
              symbols.forEach((s, symbolIndex) => {
                s.textContent = fallbackSymbols[symbolIndex];
              });
              reel.classList.remove("spinning");
              resolve();
            });
        }
      }, 80);
    });
  });

  // Esperar a que todos los rodillos terminen
  await Promise.all(spinPromises);

  // Enviar spin al servidor con autenticación
  try {
    const spinResponse = await fetch(`${API_URL}/spin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({ bet: bet })
    });

    if (!spinResponse.ok) {
      if (spinResponse.status === 401) {
        logout();
        return;
      }
      const error = await spinResponse.json();
      setStatus(`❌ ${error.detail || 'Error'}`);
      // Restaurar balance anterior
      balance = balanceAnterior;
      updateBalance();
      spinning = false;
      return;
    }

    const serverData = await spinResponse.json();
    const win = serverData.win;

    // ACTUALIZAR SALDO DESDE EL SERVIDOR
    balance = serverData.nuevo_saldo;
    updateBalance();

    // Efecto de victoria o pérdida
    if (win > 0) {
      const winAmount = win;
      const isBigWin = winAmount >= bet * 5;

      if (isBigWin) {
        // GRAN VICTORIA
        setStatus(`🎊 ¡GRAN VICTORIA! +$${winAmount} 🎊`);

        // Sonido de gran victoria
        if (typeof soundManager !== 'undefined') {
          soundManager.playBigWinSound();
          setTimeout(() => soundManager.playCoinSound(), 400);
        }

        document.querySelector('.slot-machine').classList.add('machine-shake-win');
        setTimeout(() => {
          document.querySelector('.slot-machine').classList.remove('machine-shake-win');
        }, 500);

        createFlash();
        createCelebrationOverlay();
        createBigWinText(`¡$${winAmount}!`);
        createConfetti(50);

        document.querySelector('.lights').classList.add('victory-lights');
        setTimeout(() => {
          document.querySelector('.lights').classList.remove('victory-lights');
        }, 3000);

      } else {
        // Victoria normal
        setStatus(`🎉 ¡GANASTE $${winAmount}!`);

        // Sonido de victoria normal
        if (typeof soundManager !== 'undefined') {
          soundManager.playWinSound();
          setTimeout(() => soundManager.playCoinSound(), 200);
        }

        gridEl.parentElement.classList.add("win-effect");
        setTimeout(() => {
          gridEl.parentElement.classList.remove("win-effect");
        }, 500);

        createConfetti(20);
        createFlash();
      }

      highlightWinningLines(finalGrid);

    } else {
      // PÉRDIDA
      setStatus("Intenta de nuevo...");

      // Sonido de pérdida
      if (typeof soundManager !== 'undefined') {
        soundManager.playLossSound();
      }

      createLossOverlay();

      document.querySelector('.slot-machine').classList.add('machine-shake-loss');
      setTimeout(() => {
        document.querySelector('.slot-machine').classList.remove('machine-shake-loss');
      }, 400);

      const symbols = document.querySelectorAll('.symbol');
      symbols.forEach(s => s.classList.add('symbol-dimmed'));
      setTimeout(() => {
        symbols.forEach(s => s.classList.remove('symbol-dimmed'));
      }, 800);

      createLossText();
    }

  } catch (error) {
    console.error('Error en spin:', error);
    setStatus('❌ Error de conexión');
    // Restaurar balance anterior
    balance = balanceAnterior;
    updateBalance();
  }

  spinning = false;

  if (autoSpin && balance >= bet) {
    setTimeout(() => {
      pullLever();
    }, 1000);
  } else if (autoSpin && balance < bet) {
    autoSpin = false;
    autoBtn.querySelector('.auto-status').textContent = "OFF";
    setStatus("💸 Sin saldo para auto-spin");
  }
}

// Resaltar líneas ganadoras
function highlightWinningLines(grid) {
  const cells = document.querySelectorAll('.cell');
  let blinkCount = 0;
  const blinkInterval = setInterval(() => {
    cells.forEach((cell, i) => {
      if (blinkCount % 2 === 0) {
        cell.style.borderColor = '#ab925c';
        cell.style.boxShadow = '0 0 20px rgba(171, 146, 92, 0.8), inset 0 0 20px rgba(171, 146, 92, 0.3)';
      } else {
        cell.style.borderColor = '#8b7a4c';
        cell.style.boxShadow = 'inset 0 2px 4px rgba(171, 146, 92, 0.2), 0 4px 8px rgba(0, 0, 0, 0.5)';
      }
    });
    blinkCount++;
    if (blinkCount >= 6) {
      clearInterval(blinkInterval);
      cells.forEach(cell => {
        cell.style.borderColor = '';
        cell.style.boxShadow = '';
      });
    }
  }, 200);
}

// Toggle auto-spin
autoBtn.onclick = () => {
  autoSpin = !autoSpin;
  autoBtn.querySelector('.auto-status').textContent = autoSpin ? "ON" : "OFF";

  if (autoSpin) {
    autoBtn.style.background = "linear-gradient(145deg, #1a4d1a, #0d3d0d)";
    autoBtn.style.borderColor = "#00FF00";
    pullLever();
  } else {
    autoBtn.style.background = "";
    autoBtn.style.borderColor = "";
  }
};

// Inicializar
loadBalance();
updateBalance();
setStatus("¡Buena suerte!");
