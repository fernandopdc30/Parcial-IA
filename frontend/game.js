// ================================================================
// game.js — Dino Runner GA
// Frontend: conexión WebSocket, renderizado Canvas, actualización HUD
// El backend es quien corre el AG y la física; aquí solo dibujamos.
// ================================================================

'use strict';

// ── Constantes de renderizado (deben coincidir con backend/config.py) ────────
const SUELO_Y       = 340;    // Coordenada Y del suelo
const AVATAR_ALTO   = 40;     // Alto del bounding box del avatar
const AVATAR_ANCHO  = 20;     // Ancho del bounding box del avatar
const CANVAS_W      = 800;
const CANVAS_H      = 400;

// Colores del juego
const COLOR_VIVO    = 'rgba(74, 144, 226, 0.70)';   // Azul semitransparente
const COLOR_MEJOR   = '#FFD700';                      // Dorado sólido
const COLOR_SUELO_A = '#3a6644';                      // Verde oscuro (suelo)
const COLOR_SUELO_B = '#4a7c59';                      // Verde claro (franja superior)

// ── Estado global ─────────────────────────────────────────────────────────────
let socket      = null;    // Conexión WebSocket
let estadoJuego = null;    // Último mensaje "estado" recibido del servidor
let frameNum    = 0;       // Contador de frames para animaciones
let soloMejor   = false;   // Toggle: mostrar solo el mejor avatar

// ── Referencias al DOM ────────────────────────────────────────────────────────
const gameCanvas  = document.getElementById('gameCanvas');
const ctx         = gameCanvas.getContext('2d');
const chartCanvas = document.getElementById('chartCanvas');
const ctxChart    = chartCanvas.getContext('2d');
const connStatus  = document.getElementById('conn-status');
const btnRein     = document.getElementById('btn-reiniciar');
const btnToggle   = document.getElementById('btn-toggle');
const elGen       = document.getElementById('stat-gen');
const elVivos     = document.getElementById('stat-vivos');
const elFitAct    = document.getElementById('stat-fitness-actual');
const elFitHist   = document.getElementById('stat-fitness-hist');
const elCrom      = document.getElementById('stat-cromosoma');

// ================================================================
// CONEXIÓN WEBSOCKET
// ================================================================

/**
 * Abre la conexión WebSocket con el servidor.
 * Detecta automáticamente ws:// o wss:// según el protocolo de la página.
 * Si la conexión se cierra, reintenta después de 2 segundos.
 */
function conectar() {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const url   = `${proto}://${window.location.host}/ws`;

  socket = new WebSocket(url);

  socket.onopen = () => {
    connStatus.textContent = '🟢 Conectado';
    connStatus.className   = 'connected';
  };

  socket.onclose = () => {
    connStatus.textContent = '⚫ Reconectando...';
    connStatus.className   = 'disconnected';
    setTimeout(conectar, 2000);
  };

  socket.onerror = () => {
    socket.close();
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.tipo === 'estado') {
        estadoJuego = msg;
      }
    } catch (e) {
      console.error('[WS] Error al parsear mensaje:', e);
    }
  };
}

/**
 * Envía un mensaje de control al servidor (si la conexión está abierta).
 * @param {string} tipo - Tipo del mensaje ("reiniciar" o "toggle_vista")
 */
function enviarMensaje(tipo) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ tipo }));
  }
}

// ================================================================
// BOTONES DE CONTROL
// ================================================================

btnRein.addEventListener('click', () => {
  enviarMensaje('reiniciar');
});

btnToggle.addEventListener('click', () => {
  soloMejor = !soloMejor;
  btnToggle.textContent = soloMejor ? '👁 Mostrar Todos' : '👁 Solo el Mejor';
  btnToggle.classList.toggle('active', soloMejor);
  enviarMensaje('toggle_vista');  // Informativo; el backend no necesita actuar
});

// ================================================================
// RENDERIZADO DEL FONDO Y SUELO
// ================================================================

/**
 * Dibuja el fondo del cielo (gradiente) y la franja del suelo.
 */
function dibujarFondo() {
  // Gradiente de cielo de arriba a abajo
  const gradCielo = ctx.createLinearGradient(0, 0, 0, SUELO_Y);
  gradCielo.addColorStop(0, '#0e0e25');
  gradCielo.addColorStop(1, '#1a1a3e');
  ctx.fillStyle = gradCielo;
  ctx.fillRect(0, 0, CANVAS_W, SUELO_Y);

  // Franja del suelo (terreno)
  ctx.fillStyle = COLOR_SUELO_A;
  ctx.fillRect(0, SUELO_Y, CANVAS_W, CANVAS_H - SUELO_Y);

  // Línea superior del suelo (más clara)
  ctx.fillStyle = COLOR_SUELO_B;
  ctx.fillRect(0, SUELO_Y, CANVAS_W, 3);

  // Línea de horizonte sutil
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
  ctx.lineWidth   = 1;
  ctx.beginPath();
  ctx.moveTo(0, SUELO_Y);
  ctx.lineTo(CANVAS_W, SUELO_Y);
  ctx.stroke();
}

// ================================================================
// RENDERIZADO DEL AVATAR (figura de palo con polígonos Canvas)
// ================================================================

/**
 * Dibuja un avatar como figura de palo animada.
 *
 * Estructura (de abajo hacia arriba):
 *   - Piernas: dos rectángulos con leve rotación alternada (animación de carrera)
 *   - Cuerpo:  rectángulo vertical
 *   - Brazos:  dos líneas diagonales con oscilación
 *   - Cabeza:  círculo
 *
 * La base (pies) está en (x + AVATAR_ANCHO/2, y).
 *
 * @param {number}  x        - Posición X del borde izquierdo del avatar
 * @param {number}  y        - Posición Y de la BASE del avatar (pies)
 * @param {boolean} esMejor  - Si true, se renderiza en dorado
 * @param {number}  frame    - Contador global de frames (para animación)
 */
function dibujarAvatar(x, y, esMejor, frame) {
  const color     = esMejor ? COLOR_MEJOR : COLOR_VIVO;
  const borde     = esMejor ? 'rgba(255,200,0,0.9)' : 'rgba(74,144,226,0.9)';
  const cx        = x + AVATAR_ANCHO / 2;  // Centro horizontal

  ctx.save();
  ctx.fillStyle   = color;
  ctx.strokeStyle = borde;

  // ── PIERNAS (animación de carrera) ────────────────────────────
  const piernaW = 4;
  const piernaH = 14;
  const piernaY = y - 14;   // Punto de arranque de las piernas (cadera)
  const oscP    = Math.sin(frame * 0.25) * 0.22;  // Oscilación angular en radianes

  ctx.lineWidth = 1;

  // Pierna izquierda
  ctx.save();
  ctx.translate(cx - 3, piernaY);
  ctx.rotate(-oscP);
  ctx.fillRect(-piernaW / 2, 0, piernaW, piernaH);
  ctx.restore();

  // Pierna derecha (fase opuesta)
  ctx.save();
  ctx.translate(cx + 3, piernaY);
  ctx.rotate(oscP);
  ctx.fillRect(-piernaW / 2, 0, piernaW, piernaH);
  ctx.restore();

  // ── CUERPO ────────────────────────────────────────────────────
  const cuerpoW = 8;
  const cuerpoH = 16;
  const cuerpoX = cx - cuerpoW / 2;
  const cuerpoY = y - 14 - cuerpoH;  // Encima de las piernas

  ctx.fillRect(cuerpoX, cuerpoY, cuerpoW, cuerpoH);

  // ── BRAZOS (líneas con oscilación) ────────────────────────────
  const ombrosY = cuerpoY + 4;
  const oscB    = Math.sin(frame * 0.25 + Math.PI) * 5;  // Fase opuesta a piernas
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  // Brazo izquierdo
  ctx.moveTo(cuerpoX, ombrosY);
  ctx.lineTo(cuerpoX - 7, ombrosY + 7 + oscB);
  // Brazo derecho
  ctx.moveTo(cuerpoX + cuerpoW, ombrosY);
  ctx.lineTo(cuerpoX + cuerpoW + 7, ombrosY + 7 - oscB);
  ctx.stroke();

  // ── CABEZA ────────────────────────────────────────────────────
  const radioC  = 7;
  const cabezaY = cuerpoY - radioC - 1;

  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(cx, cabezaY, radioC, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Ojo (pequeño punto blanco)
  ctx.fillStyle = esMejor ? '#1a0a00' : 'rgba(255,255,255,0.8)';
  ctx.beginPath();
  ctx.arc(cx + 3, cabezaY - 1, 2, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

// ================================================================
// RENDERIZADO DEL OBSTÁCULO
// ================================================================

/**
 * Dibuja un obstáculo como un bloque rojo con gradiente y sombra.
 * @param {{ x: number, y: number, ancho: number, alto: number }} obs
 */
function dibujarObstaculo(obs) {
  ctx.save();

  // Gradiente de izquierda a derecha
  const grad = ctx.createLinearGradient(obs.x, obs.y, obs.x + obs.ancho, obs.y);
  grad.addColorStop(0, '#c0302a');
  grad.addColorStop(0.5, '#e74c3c');
  grad.addColorStop(1, '#c0302a');
  ctx.fillStyle = grad;
  ctx.fillRect(obs.x, obs.y, obs.ancho, obs.alto);

  // Franja superior más clara (brillo)
  ctx.fillStyle = 'rgba(255, 120, 110, 0.5)';
  ctx.fillRect(obs.x + 1, obs.y + 1, obs.ancho - 2, 4);

  // Sombra en la base
  ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
  ctx.fillRect(obs.x + 2, obs.y + obs.alto - 3, obs.ancho - 2, 3);

  ctx.restore();
}

// ================================================================
// GRÁFICO DE HISTORIAL DE FITNESS (Canvas 2D puro)
// ================================================================

/**
 * Dibuja el gráfico de línea del historial de mejor fitness por generación.
 * Implementado completamente con Canvas 2D, sin librerías externas.
 *
 * @param {number[]} historial - Array de valores de fitness (últimas generaciones)
 */
function dibujarGrafico(historial) {
  const w   = chartCanvas.width;
  const h   = chartCanvas.height;
  const pad = { top: 12, right: 8, bottom: 20, left: 38 };

  ctxChart.clearRect(0, 0, w, h);

  // Fondo
  ctxChart.fillStyle = '#080e1e';
  ctxChart.fillRect(0, 0, w, h);

  if (!historial || historial.length === 0) {
    ctxChart.fillStyle  = '#445566';
    ctxChart.font       = '10px sans-serif';
    ctxChart.textAlign  = 'center';
    ctxChart.fillText('Sin datos todavía…', w / 2, h / 2);
    return;
  }

  const datos  = historial.slice(-20);   // Últimas 20 generaciones
  const maxVal = Math.max(...datos, 1);
  const areaW  = w - pad.left - pad.right;
  const areaH  = h - pad.top - pad.bottom;

  /** Convierte un valor de fitness a coordenada Y en el canvas */
  const mapY = (v) => pad.top + areaH - (v / maxVal) * areaH;
  /** Convierte un índice a coordenada X en el canvas */
  const mapX = (i) => pad.left + (datos.length > 1 ? (i / (datos.length - 1)) * areaW : areaW / 2);

  // ── Líneas de grid ────────────────────────────────────────────
  ctxChart.strokeStyle = 'rgba(255,255,255,0.06)';
  ctxChart.lineWidth   = 1;
  for (let i = 0; i <= 3; i++) {
    const yG = pad.top + (areaH / 3) * i;
    ctxChart.beginPath();
    ctxChart.moveTo(pad.left, yG);
    ctxChart.lineTo(w - pad.right, yG);
    ctxChart.stroke();
  }

  // ── Etiquetas eje Y ───────────────────────────────────────────
  ctxChart.fillStyle = '#5566aa';
  ctxChart.font      = '9px monospace';
  ctxChart.textAlign = 'right';
  const labelMax = maxVal >= 1000 ? `${(maxVal / 1000).toFixed(1)}k` : String(Math.round(maxVal));
  ctxChart.fillText(labelMax, pad.left - 3, pad.top + 5);
  ctxChart.fillText('0', pad.left - 3, h - pad.bottom + 4);

  // ── Área rellena bajo la curva ────────────────────────────────
  const gradArea = ctxChart.createLinearGradient(0, pad.top, 0, h - pad.bottom);
  gradArea.addColorStop(0, 'rgba(74, 144, 226, 0.45)');
  gradArea.addColorStop(1, 'rgba(74, 144, 226, 0.02)');

  ctxChart.beginPath();
  ctxChart.moveTo(mapX(0), h - pad.bottom);
  datos.forEach((v, i) => ctxChart.lineTo(mapX(i), mapY(v)));
  ctxChart.lineTo(mapX(datos.length - 1), h - pad.bottom);
  ctxChart.closePath();
  ctxChart.fillStyle = gradArea;
  ctxChart.fill();

  // ── Línea de la curva ─────────────────────────────────────────
  ctxChart.beginPath();
  ctxChart.strokeStyle = '#4A90E2';
  ctxChart.lineWidth   = 1.8;
  ctxChart.lineJoin    = 'round';
  ctxChart.lineCap     = 'round';
  datos.forEach((v, i) => {
    if (i === 0) ctxChart.moveTo(mapX(i), mapY(v));
    else         ctxChart.lineTo(mapX(i), mapY(v));
  });
  ctxChart.stroke();

  // ── Punto en el último valor (resaltado dorado) ───────────────
  const ux = mapX(datos.length - 1);
  const uy = mapY(datos[datos.length - 1]);
  ctxChart.beginPath();
  ctxChart.arc(ux, uy, 3.5, 0, Math.PI * 2);
  ctxChart.fillStyle = '#FFD700';
  ctxChart.fill();

  // ── Etiqueta del eje X ────────────────────────────────────────
  ctxChart.fillStyle = '#5566aa';
  ctxChart.font      = '9px monospace';
  ctxChart.textAlign = 'center';
  ctxChart.fillText('Generaciones', w / 2, h - 3);
}

// ================================================================
// ACTUALIZACIÓN DEL PANEL HUD
// ================================================================

/**
 * Actualiza todos los elementos de texto del panel lateral con los
 * datos estadísticos recibidos del servidor.
 *
 * @param {{ generacion, vivos, mejor_fitness_actual, mejor_fitness_historico,
 *           mejor_cromosoma, historial_fitness }} stats
 */
function actualizarHUD(stats) {
  elGen.textContent    = stats.generacion;
  elVivos.textContent  = `${stats.vivos} / 30`;
  elFitAct.textContent = stats.mejor_fitness_actual.toLocaleString('es');
  elFitHist.textContent = stats.mejor_fitness_historico.toLocaleString('es');

  const [d, v] = stats.mejor_cromosoma || [0, 0];
  elCrom.textContent = `[${d.toFixed(1)}, ${v.toFixed(2)}]`;

  dibujarGrafico(stats.historial_fitness);
}

// ================================================================
// BUCLE DE RENDERIZADO PRINCIPAL
// ================================================================

/**
 * Bucle de renderizado usando requestAnimationFrame (~60 fps).
 * Dibuja el último estado recibido del servidor sin esperar al próximo mensaje WS.
 * Esto desacopla la velocidad de renderizado de la velocidad de la red.
 */
function renderLoop() {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

  if (!estadoJuego) {
    // Pantalla de espera mientras no hay conexión
    dibujarFondo();
    ctx.fillStyle = 'rgba(200, 210, 255, 0.35)';
    ctx.font      = '18px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Conectando con el servidor…', CANVAS_W / 2, CANVAS_H / 2);
    requestAnimationFrame(renderLoop);
    return;
  }

  const { avatares, obstaculos, stats } = estadoJuego;

  // 1. Fondo
  dibujarFondo();

  // 2. Obstáculos
  obstaculos.forEach(obs => dibujarObstaculo(obs));

  // 3. Filtrar avatares según toggle "Solo el mejor"
  let avataresMostrar = avatares.filter(av => av.vivo);
  if (soloMejor) {
    avataresMostrar = avataresMostrar.filter(av => av.mejor);
  }

  // 4. Renderizar primero los normales, luego el mejor (encima de todos)
  avataresMostrar
    .filter(av => !av.mejor)
    .forEach(av => dibujarAvatar(av.x, av.y, false, frameNum));

  avataresMostrar
    .filter(av => av.mejor)
    .forEach(av => dibujarAvatar(av.x, av.y, true, frameNum));

  // 5. Actualizar panel HUD
  actualizarHUD(stats);

  frameNum++;
  requestAnimationFrame(renderLoop);
}

// ================================================================
// ARRANQUE
// ================================================================

conectar();      // Iniciar conexión WebSocket
renderLoop();    // Iniciar bucle de renderizado
