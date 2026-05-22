// ================================================================
// game.js — Dino Runner GA
// Frontend: navegación SPA, conexión WebSocket, renderizado Canvas,
//           actualización HUD y animación de preview del hero.
// ================================================================

"use strict";

// ── Constantes de renderizado ─────────────────────────────────────
const SUELO_Y     = 340;
const AVATAR_ALTO = 40;
const AVATAR_ANCHO = 20;
const CANVAS_W    = 800;
const CANVAS_H    = 400;

const COLOR_VIVO    = "rgba(74, 144, 226, 0.70)";
const COLOR_MEJOR   = "#FFD700";
const COLOR_SUELO_A = "#3a6644";
const COLOR_SUELO_B = "#4a7c59";

// ── Estado global ─────────────────────────────────────────────────
let socket         = null;
let estadoJuego    = null;
let frameNum       = 0;
let soloMejor      = false;
let mostrarSensores = true;
let factorVelocidad = 1;
let pantallaActual  = "landing";

// ================================================================
// NAVEGACIÓN SPA
// ================================================================

/**
 * Cambia entre la pantalla de landing y la de simulación.
 * También actualiza los botones activos del navbar.
 * @param {"landing"|"simulacion"} pantalla
 */
function mostrarPantalla(pantalla) {
  pantallaActual = pantalla;

  const landing = document.getElementById("screen-landing");
  const sim     = document.getElementById("screen-simulacion");
  const navInicio = document.getElementById("nav-inicio");
  const navSim    = document.getElementById("nav-sim");

  if (pantalla === "landing") {
    landing.classList.add("active", "fade-in");
    sim.classList.remove("active");
    navInicio.classList.add("active");
    navSim.classList.remove("active");
    // Limpiar clase de animación después
    setTimeout(() => landing.classList.remove("fade-in"), 400);
  } else {
    sim.classList.add("active", "fade-in");
    landing.classList.remove("active");
    navSim.classList.add("active");
    navInicio.classList.remove("active");
    setTimeout(() => sim.classList.remove("fade-in"), 400);
    // Conectar WS si no está conectado
    if (!socket || socket.readyState === WebSocket.CLOSED) {
      conectar();
    }
  }

  // Scroll al inicio siempre
  window.scrollTo({ top: 0, behavior: "instant" });
}

/**
 * Hace scroll suave a una sección del landing por su ID.
 * @param {string} sectionId
 */
function scrollToSection(sectionId) {
  setTimeout(() => {
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 50);
}

// Exponer funciones al HTML (onclick="...")
window.mostrarPantalla  = mostrarPantalla;
window.scrollToSection  = scrollToSection;

// ================================================================
// ANIMACIÓN DE PREVIEW (hero landing)
// ================================================================

const previewCanvas = document.getElementById("previewCanvas");
const ctxPrev = previewCanvas.getContext("2d");
const PW = 420, PH = 200;
const PSUELO = 155; // Suelo en el mini canvas

// Estado de la preview
const prevAvatares = [
  { x: 60,  y: PSUELO, vy: 0, fase: 0,   color: "rgba(74,144,226,0.8)",  esMejor: false },
  { x: 85,  y: PSUELO, vy: 0, fase: 40,  color: "rgba(74,144,226,0.55)", esMejor: false },
  { x: 40,  y: PSUELO, vy: 0, fase: 80,  color: "rgba(74,144,226,0.4)",  esMejor: false },
  { x: 70,  y: PSUELO, vy: 0, fase: 120, color: "#FFD700",               esMejor: true  },
];
let prevObsX = PW + 40;
let prevObsW = 18, prevObsH = 36;
let prevObsVel = 2.8;
let prevFrame  = 0;

function dibujarPreviewFondo() {
  // Cielo
  const g = ctxPrev.createLinearGradient(0, 0, 0, PSUELO);
  g.addColorStop(0, "#0e0e25");
  g.addColorStop(1, "#1a1a3e");
  ctxPrev.fillStyle = g;
  ctxPrev.fillRect(0, 0, PW, PSUELO);
  // Suelo
  ctxPrev.fillStyle = "#3a6644";
  ctxPrev.fillRect(0, PSUELO, PW, PH - PSUELO);
  ctxPrev.fillStyle = "#4a7c59";
  ctxPrev.fillRect(0, PSUELO, PW, 2);
}

function dibujarPrevAvatar(av, frame) {
  const cx = av.x + 8;
  const y  = av.y;
  ctxPrev.save();
  ctxPrev.fillStyle   = av.color;
  ctxPrev.strokeStyle = av.color;

  // Piernas
  const oscP = Math.sin(frame * 0.25) * 0.2;
  const piY  = y - 7;
  ctxPrev.save(); ctxPrev.translate(cx - 2, piY); ctxPrev.rotate(-oscP);
  ctxPrev.fillRect(-2, 0, 3, 7); ctxPrev.restore();
  ctxPrev.save(); ctxPrev.translate(cx + 2, piY); ctxPrev.rotate(oscP);
  ctxPrev.fillRect(-2, 0, 3, 7); ctxPrev.restore();

  // Cuerpo
  ctxPrev.fillRect(cx - 4, y - 7 - 9, 7, 9);

  // Brazos
  const oscB = Math.sin(frame * 0.25 + Math.PI) * 3;
  ctxPrev.lineWidth = 1.5;
  ctxPrev.beginPath();
  ctxPrev.moveTo(cx - 4, y - 12);
  ctxPrev.lineTo(cx - 8, y - 9 + oscB);
  ctxPrev.moveTo(cx + 3,  y - 12);
  ctxPrev.lineTo(cx + 7,  y - 9 - oscB);
  ctxPrev.stroke();

  // Cabeza
  ctxPrev.beginPath();
  ctxPrev.arc(cx, y - 7 - 9 - 4, 4, 0, Math.PI * 2);
  ctxPrev.fill();
  ctxPrev.restore();
}

function dibujarPrevObstaculo(x) {
  ctxPrev.save();
  const g = ctxPrev.createLinearGradient(x, 0, x + prevObsW, 0);
  g.addColorStop(0,   "#c0302a");
  g.addColorStop(0.5, "#e74c3c");
  g.addColorStop(1,   "#c0302a");
  ctxPrev.fillStyle = g;
  ctxPrev.fillRect(x, PSUELO - prevObsH, prevObsW, prevObsH);
  ctxPrev.fillStyle = "rgba(255,120,110,0.4)";
  ctxPrev.fillRect(x + 1, PSUELO - prevObsH + 1, prevObsW - 2, 3);
  ctxPrev.restore();
}

let prevAnimId = null;

function animarPreview() {
  ctxPrev.clearRect(0, 0, PW, PH);
  dibujarPreviewFondo();

  prevFrame++;
  prevObsX -= prevObsVel;

  // Reiniciar obstáculo
  if (prevObsX + prevObsW < 0) {
    prevObsX  = PW + 20;
    prevObsW  = 15 + Math.random() * 20;
    prevObsH  = 20 + Math.random() * 30;
  }

  // Lógica de salto simple para los avatares de preview
  prevAvatares.forEach((av) => {
    const dist = prevObsX - av.x;
    const umbral = 70 + (av.esMejor ? 10 : Math.random() * 30 - 10);

    if (av.y >= PSUELO && dist > 0 && dist < umbral) {
      av.vy = -5.5;
    }
    av.vy += 0.28; // gravedad
    av.y  += av.vy;
    if (av.y >= PSUELO) {
      av.y  = PSUELO;
      av.vy = 0;
    }

    // Indicador de salto
    if (av.y < PSUELO - 2) {
      ctxPrev.save();
      ctxPrev.font = "bold 9px sans-serif";
      ctxPrev.textAlign = "center";
      ctxPrev.fillStyle = av.esMejor ? "#FFD700" : "rgba(140,200,255,0.9)";
      ctxPrev.fillText("↑", av.x + 8, av.y - 24);
      ctxPrev.restore();
    }

    dibujarPrevAvatar(av, prevFrame + av.fase);
  });

  dibujarPrevObstaculo(prevObsX);

  // Overlay con texto de generación simulada
  const gen = Math.floor(prevFrame / 120) + 1;
  ctxPrev.save();
  ctxPrev.fillStyle = "rgba(0,0,0,0.45)";
  ctxPrev.fillRect(0, 0, PW, 26);
  ctxPrev.font = "bold 10px 'Inter', sans-serif";
  ctxPrev.fillStyle = "rgba(255,215,0,0.85)";
  ctxPrev.textAlign = "left";
  ctxPrev.fillText(`Generación ${gen}`, 10, 17);
  ctxPrev.textAlign = "right";
  ctxPrev.fillStyle = "rgba(74,144,226,0.85)";
  ctxPrev.fillText(`${prevAvatares.length} avatares`, PW - 10, 17);
  ctxPrev.restore();

  prevAnimId = requestAnimationFrame(animarPreview);
}

// Iniciar animación de preview al cargar
animarPreview();

// ================================================================
// REFERENCIAS AL DOM — SIMULACIÓN
// ================================================================
const gameCanvas    = document.getElementById("gameCanvas");
const ctx           = gameCanvas.getContext("2d");
const chartCanvas   = document.getElementById("chartCanvas");
const ctxChart      = chartCanvas.getContext("2d");
const connStatus    = document.getElementById("conn-status");
const btnRein       = document.getElementById("btn-reiniciar");
const btnToggle     = document.getElementById("btn-toggle");
const scatterCanvas = document.getElementById("scatterCanvas");
const ctxScatter    = scatterCanvas.getContext("2d");
const btnSensores   = document.getElementById("btn-sensores");
const speedBtns     = document.querySelectorAll(".btn-speed");
const elGen         = document.getElementById("stat-gen");
const elVivos       = document.getElementById("stat-vivos");
const elFitAct      = document.getElementById("stat-fitness-actual");
const elFitHist     = document.getElementById("stat-fitness-hist");
const elCrom        = document.getElementById("stat-cromosoma");

// ================================================================
// CONEXIÓN WEBSOCKET
// ================================================================

/**
 * Abre la conexión WebSocket con el servidor.
 * Detecta ws:// o wss:// según el protocolo de la página.
 * Reintenta automáticamente cada 2 segundos si se cierra.
 */
function conectar() {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const url   = `${proto}://${window.location.host}/ws`;

  socket = new WebSocket(url);

  socket.onopen = () => {
    connStatus.textContent = "🟢 Conectado";
    connStatus.className   = "connected";
  };

  socket.onclose = () => {
    connStatus.textContent = "⚫ Reconectando...";
    connStatus.className   = "disconnected";
    setTimeout(conectar, 2000);
  };

  socket.onerror = () => { socket.close(); };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.tipo === "estado") estadoJuego = msg;
    } catch (e) {
      console.error("[WS] Error al parsear mensaje:", e);
    }
  };
}

/**
 * Envía un mensaje de control al servidor.
 * @param {string} tipo  - Tipo del mensaje
 * @param {object} extra - Campos adicionales opcionales
 */
function enviarMensaje(tipo, extra = {}) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ tipo, ...extra }));
  }
}

// ================================================================
// BOTONES DE CONTROL
// ================================================================

btnRein.addEventListener("click", () => enviarMensaje("reiniciar"));

btnToggle.addEventListener("click", () => {
  soloMejor = !soloMejor;
  btnToggle.textContent = soloMejor ? "👁 Mostrar Todos" : "👁 Solo el Mejor";
  btnToggle.classList.toggle("active", soloMejor);
  enviarMensaje("toggle_vista");
});

btnSensores.addEventListener("click", () => {
  mostrarSensores = !mostrarSensores;
  btnSensores.textContent = mostrarSensores
    ? "📡 Ocultar Sensores"
    : "📡 Mostrar Sensores";
  btnSensores.classList.toggle("active", mostrarSensores);
});

speedBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    const factor = parseInt(btn.dataset.factor, 10);
    factorVelocidad = factor;
    speedBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    enviarMensaje("velocidad", { factor });
  });
});

// ================================================================
// ZONA DE SENSOR (umbral_distancia visible)
// ================================================================

function dibujarSensorZona(x, umbralDistancia, esMejor) {
  if (!mostrarSensores) return;
  const startX = x + AVATAR_ANCHO;
  const zoneH  = AVATAR_ALTO + 12;
  const zoneY  = SUELO_Y - zoneH;

  ctx.fillStyle = esMejor
    ? "rgba(255, 215, 0, 0.07)"
    : "rgba(74, 144, 226, 0.05)";
  ctx.fillRect(startX, zoneY, umbralDistancia, zoneH);

  ctx.save();
  ctx.strokeStyle = esMejor
    ? "rgba(255, 215, 0, 0.55)"
    : "rgba(74, 144, 226, 0.35)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  ctx.moveTo(startX + umbralDistancia, zoneY - 6);
  ctx.lineTo(startX + umbralDistancia, SUELO_Y);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
}

// ================================================================
// INDICADOR DE SALTO INMINENTE
// ================================================================

function dibujarIndicadorSalto(x, y, esMejor) {
  if (y >= SUELO_Y - 1) return;
  const cx     = x + AVATAR_ANCHO / 2;
  const indicY = y - AVATAR_ALTO - 12;
  ctx.save();
  ctx.font          = "bold 14px sans-serif";
  ctx.textAlign     = "center";
  ctx.textBaseline  = "middle";
  ctx.shadowColor   = esMejor ? "#FFD700" : "#4A90E2";
  ctx.shadowBlur    = 8;
  ctx.fillStyle     = esMejor ? "#FFD700" : "rgba(140, 200, 255, 0.95)";
  ctx.fillText("↑", cx, indicY);
  ctx.restore();
}

// ================================================================
// SCATTER PLOT DE CROMOSOMAS
// ================================================================

function dibujarScatterPlot(cromosomas) {
  const w   = scatterCanvas.width;
  const h   = scatterCanvas.height;
  const pad = { top: 14, right: 12, bottom: 22, left: 32 };

  ctxScatter.clearRect(0, 0, w, h);
  ctxScatter.fillStyle = "#080e1e";
  ctxScatter.fillRect(0, 0, w, h);

  if (!cromosomas || cromosomas.length === 0) return;

  const areaW = w - pad.left - pad.right;
  const areaH = h - pad.top  - pad.bottom;

  const mapX = (dist) => pad.left + ((dist - 50)  / 350) * areaW;
  const mapY = (vel)  => pad.top  + areaH - (vel  / 20)  * areaH;

  // Grid
  ctxScatter.strokeStyle = "rgba(255,255,255,0.06)";
  ctxScatter.lineWidth   = 1;
  for (let i = 0; i <= 3; i++) {
    const xg = pad.left + (areaW / 3) * i;
    ctxScatter.beginPath();
    ctxScatter.moveTo(xg, pad.top);
    ctxScatter.lineTo(xg, h - pad.bottom);
    ctxScatter.stroke();
    const yg = pad.top + (areaH / 3) * i;
    ctxScatter.beginPath();
    ctxScatter.moveTo(pad.left, yg);
    ctxScatter.lineTo(w - pad.right, yg);
    ctxScatter.stroke();
  }

  // Etiquetas
  ctxScatter.fillStyle   = "#445577";
  ctxScatter.font        = "8px monospace";
  ctxScatter.textAlign   = "center";
  ctxScatter.fillText("dist →", w / 2, h - 4);
  ctxScatter.fillText("50",  pad.left,          h - pad.bottom + 10);
  ctxScatter.fillText("400", w - pad.right + 4, h - pad.bottom + 10);
  ctxScatter.save();
  ctxScatter.translate(9, h / 2);
  ctxScatter.rotate(-Math.PI / 2);
  ctxScatter.fillText("vel ↑", 0, 0);
  ctxScatter.restore();

  // Individuos (muertos → vivos → mejor)
  const muertos = cromosomas.filter((c) => !c.vivo && !c.mejor);
  const vivos   = cromosomas.filter((c) =>  c.vivo && !c.mejor);
  const mejor   = cromosomas.filter((c) =>  c.mejor);

  muertos.forEach((c) => {
    ctxScatter.beginPath();
    ctxScatter.arc(mapX(c.dist), mapY(c.vel), 2, 0, Math.PI * 2);
    ctxScatter.fillStyle = "rgba(120, 120, 140, 0.35)";
    ctxScatter.fill();
  });
  vivos.forEach((c) => {
    ctxScatter.beginPath();
    ctxScatter.arc(mapX(c.dist), mapY(c.vel), 3.5, 0, Math.PI * 2);
    ctxScatter.fillStyle = "rgba(74, 144, 226, 0.75)";
    ctxScatter.fill();
  });
  mejor.forEach((c) => {
    const px = mapX(c.dist), py = mapY(c.vel);
    ctxScatter.beginPath();
    ctxScatter.arc(px, py, 7, 0, Math.PI * 2);
    ctxScatter.fillStyle = "rgba(255, 215, 0, 0.15)";
    ctxScatter.fill();
    ctxScatter.beginPath();
    ctxScatter.arc(px, py, 4.5, 0, Math.PI * 2);
    ctxScatter.fillStyle = "#FFD700";
    ctxScatter.fill();
    ctxScatter.strokeStyle = "rgba(255,200,0,0.8)";
    ctxScatter.lineWidth   = 1.5;
    ctxScatter.stroke();
  });
}

// ================================================================
// FONDO Y SUELO
// ================================================================

function dibujarFondo() {
  const gradCielo = ctx.createLinearGradient(0, 0, 0, SUELO_Y);
  gradCielo.addColorStop(0, "#0e0e25");
  gradCielo.addColorStop(1, "#1a1a3e");
  ctx.fillStyle = gradCielo;
  ctx.fillRect(0, 0, CANVAS_W, SUELO_Y);

  ctx.fillStyle = COLOR_SUELO_A;
  ctx.fillRect(0, SUELO_Y, CANVAS_W, CANVAS_H - SUELO_Y);
  ctx.fillStyle = COLOR_SUELO_B;
  ctx.fillRect(0, SUELO_Y, CANVAS_W, 3);

  ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
  ctx.lineWidth   = 1;
  ctx.beginPath();
  ctx.moveTo(0, SUELO_Y);
  ctx.lineTo(CANVAS_W, SUELO_Y);
  ctx.stroke();
}

// ================================================================
// AVATAR (figura de palo animada)
// ================================================================

function dibujarAvatar(x, y, esMejor, frame) {
  const color  = esMejor ? COLOR_MEJOR : COLOR_VIVO;
  const borde  = esMejor ? "rgba(255,200,0,0.9)" : "rgba(74,144,226,0.9)";
  const cx     = x + AVATAR_ANCHO / 2;

  ctx.save();
  ctx.fillStyle   = color;
  ctx.strokeStyle = borde;

  // Piernas
  const piernaW = 4, piernaH = 14;
  const piernaY = y - 14;
  const oscP    = Math.sin(frame * 0.25) * 0.22;
  ctx.lineWidth  = 1;
  ctx.save(); ctx.translate(cx - 3, piernaY); ctx.rotate(-oscP);
  ctx.fillRect(-piernaW / 2, 0, piernaW, piernaH); ctx.restore();
  ctx.save(); ctx.translate(cx + 3, piernaY); ctx.rotate(oscP);
  ctx.fillRect(-piernaW / 2, 0, piernaW, piernaH); ctx.restore();

  // Cuerpo
  const cuerpoW = 8, cuerpoH = 16;
  const cuerpoX = cx - cuerpoW / 2;
  const cuerpoY = y - 14 - cuerpoH;
  ctx.fillRect(cuerpoX, cuerpoY, cuerpoW, cuerpoH);

  // Brazos
  const ombrosY = cuerpoY + 4;
  const oscB    = Math.sin(frame * 0.25 + Math.PI) * 5;
  ctx.lineWidth  = 2.5;
  ctx.beginPath();
  ctx.moveTo(cuerpoX, ombrosY);           ctx.lineTo(cuerpoX - 7, ombrosY + 7 + oscB);
  ctx.moveTo(cuerpoX + cuerpoW, ombrosY); ctx.lineTo(cuerpoX + cuerpoW + 7, ombrosY + 7 - oscB);
  ctx.stroke();

  // Cabeza
  const radioC  = 7;
  const cabezaY = cuerpoY - radioC - 1;
  ctx.lineWidth  = 1.5;
  ctx.beginPath();
  ctx.arc(cx, cabezaY, radioC, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Ojo
  ctx.fillStyle = esMejor ? "#1a0a00" : "rgba(255,255,255,0.8)";
  ctx.beginPath();
  ctx.arc(cx + 3, cabezaY - 1, 2, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

// ================================================================
// OBSTÁCULO
// ================================================================

function dibujarObstaculo(obs) {
  ctx.save();
  const grad = ctx.createLinearGradient(obs.x, obs.y, obs.x + obs.ancho, obs.y);
  grad.addColorStop(0,   "#c0302a");
  grad.addColorStop(0.5, "#e74c3c");
  grad.addColorStop(1,   "#c0302a");
  ctx.fillStyle = grad;
  ctx.fillRect(obs.x, obs.y, obs.ancho, obs.alto);
  ctx.fillStyle = "rgba(255, 120, 110, 0.5)";
  ctx.fillRect(obs.x + 1, obs.y + 1, obs.ancho - 2, 4);
  ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
  ctx.fillRect(obs.x + 2, obs.y + obs.alto - 3, obs.ancho - 2, 3);
  ctx.restore();
}

// ================================================================
// GRÁFICO DE HISTORIAL DE FITNESS
// ================================================================

function dibujarGrafico(historial) {
  const w   = chartCanvas.width;
  const h   = chartCanvas.height;
  const pad = { top: 12, right: 8, bottom: 20, left: 38 };

  ctxChart.clearRect(0, 0, w, h);
  ctxChart.fillStyle = "#080e1e";
  ctxChart.fillRect(0, 0, w, h);

  if (!historial || historial.length === 0) {
    ctxChart.fillStyle  = "#445566";
    ctxChart.font       = "10px sans-serif";
    ctxChart.textAlign  = "center";
    ctxChart.fillText("Sin datos todavía…", w / 2, h / 2);
    return;
  }

  const datos  = historial.slice(-20);
  const maxVal = Math.max(...datos, 1);
  const areaW  = w - pad.left - pad.right;
  const areaH  = h - pad.top  - pad.bottom;

  const mapY = (v) => pad.top  + areaH - (v / maxVal) * areaH;
  const mapX = (i) =>
    pad.left + (datos.length > 1 ? (i / (datos.length - 1)) * areaW : areaW / 2);

  // Grid
  ctxChart.strokeStyle = "rgba(255,255,255,0.06)";
  ctxChart.lineWidth   = 1;
  for (let i = 0; i <= 3; i++) {
    const yG = pad.top + (areaH / 3) * i;
    ctxChart.beginPath();
    ctxChart.moveTo(pad.left, yG);
    ctxChart.lineTo(w - pad.right, yG);
    ctxChart.stroke();
  }

  // Etiquetas Y
  ctxChart.fillStyle  = "#5566aa";
  ctxChart.font       = "9px monospace";
  ctxChart.textAlign  = "right";
  const labelMax = maxVal >= 1000
    ? `${(maxVal / 1000).toFixed(1)}k`
    : String(Math.round(maxVal));
  ctxChart.fillText(labelMax, pad.left - 3, pad.top + 5);
  ctxChart.fillText("0",       pad.left - 3, h - pad.bottom + 4);

  // Área bajo la curva
  const gradArea = ctxChart.createLinearGradient(0, pad.top, 0, h - pad.bottom);
  gradArea.addColorStop(0, "rgba(74, 144, 226, 0.45)");
  gradArea.addColorStop(1, "rgba(74, 144, 226, 0.02)");

  ctxChart.beginPath();
  ctxChart.moveTo(mapX(0), h - pad.bottom);
  datos.forEach((v, i) => ctxChart.lineTo(mapX(i), mapY(v)));
  ctxChart.lineTo(mapX(datos.length - 1), h - pad.bottom);
  ctxChart.closePath();
  ctxChart.fillStyle = gradArea;
  ctxChart.fill();

  // Línea de la curva
  ctxChart.beginPath();
  ctxChart.strokeStyle = "#4A90E2";
  ctxChart.lineWidth   = 1.8;
  ctxChart.lineJoin    = "round";
  ctxChart.lineCap     = "round";
  datos.forEach((v, i) => {
    if (i === 0) ctxChart.moveTo(mapX(i), mapY(v));
    else         ctxChart.lineTo(mapX(i), mapY(v));
  });
  ctxChart.stroke();

  // Punto dorado en el último valor
  const ux = mapX(datos.length - 1);
  const uy = mapY(datos[datos.length - 1]);
  ctxChart.beginPath();
  ctxChart.arc(ux, uy, 3.5, 0, Math.PI * 2);
  ctxChart.fillStyle = "#FFD700";
  ctxChart.fill();

  // Etiqueta eje X
  ctxChart.fillStyle  = "#5566aa";
  ctxChart.font       = "9px monospace";
  ctxChart.textAlign  = "center";
  ctxChart.fillText("Generaciones", w / 2, h - 3);
}

// ================================================================
// ACTUALIZACIÓN DEL PANEL HUD
// ================================================================

function actualizarHUD(stats, cromosomas) {
  elGen.textContent     = stats.generacion;
  elVivos.textContent   = `${stats.vivos} / 30`;
  elFitAct.textContent  = stats.mejor_fitness_actual.toLocaleString("es");
  elFitHist.textContent = stats.mejor_fitness_historico.toLocaleString("es");

  const [d, v] = stats.mejor_cromosoma || [0, 0];
  elCrom.textContent = `[${d.toFixed(1)}, ${v.toFixed(2)}]`;

  dibujarGrafico(stats.historial_fitness);
  dibujarScatterPlot(cromosomas);
}

// ================================================================
// BUCLE DE RENDERIZADO PRINCIPAL (Simulación)
// ================================================================

function renderLoop() {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

  if (!estadoJuego) {
    dibujarFondo();
    ctx.fillStyle  = "rgba(200, 210, 255, 0.35)";
    ctx.font       = "18px 'Inter', sans-serif";
    ctx.textAlign  = "center";
    ctx.fillText("Conectando con el servidor…", CANVAS_W / 2, CANVAS_H / 2 - 10);
    ctx.fillStyle  = "rgba(200, 210, 255, 0.18)";
    ctx.font       = "13px 'Inter', sans-serif";
    ctx.fillText("Asegúrate de que el backend está en marcha", CANVAS_W / 2, CANVAS_H / 2 + 16);
    requestAnimationFrame(renderLoop);
    return;
  }

  const { avatares, obstaculos, stats } = estadoJuego;

  // 1. Fondo
  dibujarFondo();

  // 2. Obstáculos
  obstaculos.forEach((obs) => dibujarObstaculo(obs));

  // 3. Filtrar avatares
  let avataresMostrar = avatares.filter((av) => av.vivo);
  if (soloMejor) avataresMostrar = avataresMostrar.filter((av) => av.mejor);

  // 4a. Zonas de sensor
  avataresMostrar.forEach((av) =>
    dibujarSensorZona(av.x, av.umbral_distancia, av.mejor)
  );

  // 4b. Avatares normales
  avataresMostrar
    .filter((av) => !av.mejor)
    .forEach((av) => {
      dibujarAvatar(av.x, av.y, false, frameNum);
      dibujarIndicadorSalto(av.x, av.y, false);
    });

  // 4c. Mejor avatar (encima de todos)
  avataresMostrar
    .filter((av) => av.mejor)
    .forEach((av) => {
      dibujarAvatar(av.x, av.y, true, frameNum);
      dibujarIndicadorSalto(av.x, av.y, true);
    });

  // 5. HUD
  actualizarHUD(stats, estadoJuego.cromosomas);

  frameNum++;
  requestAnimationFrame(renderLoop);
}

// ================================================================
// ARRANQUE
// ================================================================

// El WebSocket solo se conecta cuando el usuario entra a la simulación
// Para no cargar el servidor si solo se lee la página de información.

renderLoop(); // El bucle de render siempre corre (necesario para la pantalla de conexión)
