import asyncio
import time
from typing import Awaitable, Callable

from backend.application.ga_controller import GAController
from backend.config import FPS_OBJETIVO
from backend.domain.use_cases.run_simulation import tick_simulacion

# Tipo del callback que recibe el estado del juego cada tick
TickCallback = Callable[[dict], Awaitable[None]]


async def bucle_juego(
    controlador: GAController,
    on_tick: TickCallback,
    stop_event: asyncio.Event,
) -> None:
    """
    Bucle principal del juego implementado como corrutina asyncio.

    Ejecuta exactamente FPS_OBJETIVO iteraciones por segundo.
    En cada iteración (tick):
      1. Llama a tick_simulacion (física + IA + colisiones)
      2. Actualiza el contador de obstáculos superados
      3. Si todos los avatares murieron → evoluciona la generación
      4. Serializa el estado y lo envía al cliente via callback
      5. Duerme el tiempo necesario para mantener el FPS objetivo

    Args:
        controlador: Estado completo del juego (población, obstáculos, velocidad)
        on_tick: Función async que recibe el estado serializado y lo envía por WS
        stop_event: asyncio.Event; cuando se activa, el bucle termina limpiamente
    """
    intervalo_objetivo = 1.0 / FPS_OBJETIVO  # Tiempo ideal por frame (segundos)

    while not stop_event.is_set():
        tiempo_inicio = time.monotonic()

        # ── Ejecutar factor_velocidad ticks por frame visual ───────────
        # Permite acelerar la simulación (2x, 5x, 10x) sin afectar el FPS visual
        for _ in range(controlador.factor_velocidad):
            (
                controlador.obstaculos,
                controlador.velocidad_juego,
                controlador.frames_hasta_obstaculo,
            ) = tick_simulacion(
                avatares=controlador.poblacion,
                obstaculos=controlador.obstaculos,
                velocidad_juego=controlador.velocidad_juego,
                frames_hasta_obstaculo=controlador.frames_hasta_obstaculo,
            )

            # Actualizar contadores de obstáculos superados tras cada tick
            controlador.actualizar_obstaculos_superados()

            # Si todos murieron, evolucionar y salir del bucle interno
            if controlador.todos_muertos():
                controlador.evolucionar_generacion()
                break

        # ── Construir y enviar el estado al cliente ────────────────────
        estado = _construir_estado(controlador)
        try:
            await on_tick(estado)
        except Exception:
            # Si el envío falla (cliente desconectado), detener el bucle
            break

        # ── Regular velocidad del bucle para mantener FPS objetivo ─────
        tiempo_transcurrido = time.monotonic() - tiempo_inicio
        tiempo_espera = intervalo_objetivo - tiempo_transcurrido
        if tiempo_espera > 0:
            await asyncio.sleep(tiempo_espera)


def _construir_estado(controlador: GAController) -> dict:
    """
    Serializa el estado completo del juego a un diccionario JSON-serializable
    listo para enviar al cliente por WebSocket.

    Identifica al avatar con mayor fitness para marcarlo como 'mejor'
    (se renderizará en dorado en el frontend).

    Args:
        controlador: Estado actual del juego

    Returns:
        Diccionario con estructura definida en el protocolo WebSocket:
        {
          "tipo": "estado",
          "avatares": [...],
          "obstaculos": [...],
          "stats": {...}
        }
    """
    # Actualizar fitness parcial de avatares vivos sin matarlos
    for av in controlador.poblacion:
        if av.vivo:
            av.fitness = float(av.frames_sobrevividos + av.obstaculos_superados * 50)

    # Identificar el mejor avatar vivo para resaltarlo en el frontend
    avatares_vivos = [av for av in controlador.poblacion if av.vivo]
    mejor_id = -1
    if avatares_vivos:
        mejor_av = max(avatares_vivos, key=lambda a: a.fitness)
        mejor_id = mejor_av.id

    # Serializar avatares — umbral_distancia se envía para el sensor visual en canvas
    avatares_json = [
        {
            "id": av.id,
            "x": round(av.x, 1),
            "y": round(av.y, 1),
            "vivo": av.vivo,
            "mejor": av.id == mejor_id,
            "umbral_distancia": round(av.cromosoma.umbral_distancia, 1),
        }
        for av in controlador.poblacion
    ]

    # Cromosomas para el scatter plot de diversidad genética del HUD
    cromosomas_json = [
        {
            "id": av.id,
            "dist": round(av.cromosoma.umbral_distancia, 1),
            "vel": round(av.cromosoma.umbral_velocidad, 2),
            "vivo": av.vivo,
            "mejor": av.id == mejor_id,
        }
        for av in controlador.poblacion
    ]

    # Serializar obstáculos activos
    obstaculos_json = [
        {
            "x": round(obs.x, 1),
            "y": round(obs.y, 1),
            "ancho": round(obs.ancho, 1),
            "alto": round(obs.alto, 1),
        }
        for obs in controlador.obstaculos
    ]

    return {
        "tipo": "estado",
        "avatares": avatares_json,
        "obstaculos": obstaculos_json,
        "cromosomas": cromosomas_json,
        "stats": controlador.obtener_stats(),
    }
