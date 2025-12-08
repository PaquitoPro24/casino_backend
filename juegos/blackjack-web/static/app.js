// static/app.js

// ===== CAPA DE SEGURIDAD =====
// Prevenir teclas de desarrollador y atajos
document.addEventListener('keydown', function (e) {
  // F12 - DevTools
  if (e.key === 'F12' || e.keyCode === 123) {
    e.preventDefault();
    return false;
  }

  // Ctrl+Shift+I - Inspector
  // Ctrl+Shift+J - Console
  // Ctrl+Shift+C - Selector de elementos
  // Ctrl+U - Ver código fuente
  if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {
    e.preventDefault();
    return false;
  }

  if (e.ctrlKey && e.key === 'u') {
    e.preventDefault();
    return false;
  }

  // Ctrl+S - Guardar página
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    return false;
  }

  // Ctrl+P - Imprimir
  if (e.ctrlKey && e.key === 'p') {
    e.preventDefault();
    return false;
  }
});

// Prevenir clic derecho (menú contextual)
document.addEventListener('contextmenu', function (e) {
  e.preventDefault();
  return false;
});

// Prevenir selección de texto
document.addEventListener('selectstart', function (e) {
  e.preventDefault();
  return false;
});

// Prevenir copiar
document.addEventListener('copy', function (e) {
  e.preventDefault();
  return false;
});

// Prevenir cortar
document.addEventListener('cut', function (e) {
  e.preventDefault();
  return false;
});

// Prevenir pegar
document.addEventListener('paste', function (e) {
  e.preventDefault();
  return false;
});

// Prevenir arrastre
document.addEventListener('dragstart', function (e) {
  e.preventDefault();
  return false;
});

// Detectar si DevTools está abierto (método adicional)
(function () {
  const devtools = /./;
  devtools.toString = function () {
    this.opened = true;
  };

  const checkDevTools = setInterval(function () {
    console.log('%c', devtools);
    if (devtools.opened) {
      // DevTools detectado - puedes agregar acciones aquí si lo deseas
      devtools.opened = false;
    }
  }, 1000);
})();

// Deshabilitar console.log en producción (opcional)
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
  console.log = function () { };
  console.warn = function () { };
  console.error = function () { };
  console.info = function () { };
  console.debug = function () { };
}
// ===== FIN CAPA DE SEGURIDAD =====

async function api(path, body, method = "POST") {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: 'include',  // CLAVE: Envía cookies automáticamente
    body: body ? JSON.stringify(body) : null
  });

  if (res.status === 401) {
    console.warn("⚠️ No autenticado. Se requiere acceso previo o parámetro user_email.");
    // No redirigir a login, solo loguear.
    return { error: "Unauthorized" };
  }

  return await res.json();
}

function renderCard(card, hidden, index = 0) {
  const div = document.createElement("div");
  if (hidden) {
    div.className = "card back";
    div.textContent = "RC";
    div.style.animationDelay = `${index * 0.1}s`;
    return div;
  }

  const [rank, suit] = card;
  const isRed = suit === "♥" || suit === "♦";
  div.className = "card " + (isRed ? "red" : "black");
  div.style.animationDelay = `${index * 0.1}s`;

  const corner = document.createElement("div");
  corner.className = "corner";
  corner.textContent = rank + suit;
  const centerSuit = document.createElement("div");
  centerSuit.className = "suit";
  centerSuit.textContent = suit;

  div.appendChild(corner);
  div.appendChild(centerSuit);
  return div;
}

function renderState(state) {
  // referencias
  const dealerCards = document.getElementById("dealer-cards");
  const playerCards = document.getElementById("player-cards");
  const dealerVal = document.getElementById("dealer-value");
  const playerVal = document.getElementById("player-value");
  const message = document.getElementById("message");
  const betAmount = document.getElementById("bet-amount");
  const bankAmount = document.getElementById("bank-amount");
  const btnMain = document.getElementById("btn-main");
  const btnDouble = document.getElementById("btn-double");
  const btnHit = document.getElementById("btn-hit");
  const btnStand = document.getElementById("btn-stand");
  const clearBet = document.getElementById("clear-bet");

  dealerCards.innerHTML = "";
  playerCards.innerHTML = "";

  // Dealer cards
  state.dealer.forEach((card, index) => {
    const hidden = state.dealer_hidden && index === 1;
    dealerCards.appendChild(renderCard(card, hidden, index));
  });

  // Player cards
  state.player.forEach((card, index) => {
    playerCards.appendChild(renderCard(card, false, index));
  });

  // Values
  dealerVal.textContent = (state.dealer_hidden) ? "?" : (state.dealer_value || "");
  playerVal.textContent = state.player.length ? state.player_value : "";

  // Message
  message.textContent = state.message || "";

  // Bet / bank
  betAmount.textContent = "$" + state.bet;
  bankAmount.textContent = "$" + state.bank;

  // Actions
  const actions = state.allowed_actions || [];
  const can = a => actions.includes(a);

  btnDouble.disabled = !can("double");
  btnHit.disabled = !can("hit");
  btnStand.disabled = !can("stand");
  clearBet.disabled = !can("clear_bet");

  if (state.phase === "BETTING") {
    btnMain.textContent = "REPARTIR";
    btnMain.disabled = !can("deal");
  } else if (state.phase === "END") {
    btnMain.textContent = "NUEVA RONDA";
    btnMain.disabled = !can("new_round");
  } else {
    btnMain.textContent = "REPARTIR";
    btnMain.disabled = true;
  }
}

async function loadState() {
  const state = await api("/api/state", null, "GET");
  renderState(state);
}

async function setup() {
  await loadState();

  // Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", async () => {
      const amount = parseInt(chip.dataset.amount);
      const state = await api("/api/bet", { amount });
      renderState(state);
    });
  });

  document.getElementById("clear-bet").addEventListener("click", async () => {
    const state = await api("/api/clear_bet", {});
    renderState(state);
  });

  // botones laterales
  document.getElementById("btn-double").addEventListener("click", async () => {
    const state = await api("/api/double", {});
    renderState(state);
  });
  document.getElementById("btn-hit").addEventListener("click", async () => {
    const state = await api("/api/hit", {});
    renderState(state);
  });
  document.getElementById("btn-stand").addEventListener("click", async () => {
    const state = await api("/api/stand", {});
    renderState(state);
  });

  // botón principal
  document.getElementById("btn-main").addEventListener("click", async () => {
    const current = await api("/api/state", null, "GET");
    let state;
    if (current.phase === "BETTING") {
      state = await api("/api/deal", {});
    } else if (current.phase === "END") {
      state = await api("/api/new_round", {});
    } else {
      return;
    }
    renderState(state);
  });
}

setup();

