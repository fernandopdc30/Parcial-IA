import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from backend.application.ga_controller import GAController
from backend.application.game_loop import bucle_juego
from backend.infrastructure.best_chromosome_storage import (
    cargar_mejor_cromosoma,
    guardar_mejor_cromosoma,
)


async def manejar_websocket(websocket: WebSocket) -> None:
    """
    Manejador principal de la conexión WebSocket para una sesión de juego.

    Ciclo de vida de la conexión:
      1. Acepta la conexión entrante del cliente
      2. Crea un GAController independiente para esta sesión
      3. Carga el mejor cromosoma histórico si existe en disco
      4. Lanza el bucle del juego como tarea asyncio concurrente
      5. Escucha mensajes de control del cliente en el bucle principal
         - "reiniciar": cancela el bucle actual y reinicia el AG
         - "toggle_vista": el frontend lo maneja localmente, el backend lo ignora
      6. Al desconectarse: cancela el bucle y persiste el mejor cromosoma

    Args:
        websocket: Conexión WebSocket activa del cliente
    """
    await websocket.accept()

    # Crear un controlador de juego independiente para esta sesión
    controlador = GAController()

    # Restaurar el mejor fitness histórico de sesiones anteriores (si existe)
    datos_previos = cargar_mejor_cromosoma()
    if datos_previos is not None:
        cromosoma_previo, fitness_previo = datos_previos
        if fitness_previo > controlador.mejor_fitness_historico:
            controlador.mejor_fitness_historico = fitness_previo
            controlador.mejor_cromosoma_historico = cromosoma_previo

    # Evento para detener el bucle del juego limpiamente
    stop_event = asyncio.Event()

    async def enviar_estado(estado: dict) -> None:
        """Serializa y envía el estado del juego al cliente por WebSocket."""
        await websocket.send_text(json.dumps(estado))

    # Lanzar el bucle del juego como tarea asyncio concurrente
    tarea_juego = asyncio.create_task(
        bucle_juego(controlador, enviar_estado, stop_event)
    )

    try:
        # Escuchar mensajes del cliente en paralelo con el bucle del juego
        async for mensaje_raw in websocket.iter_text():
            try:
                mensaje = json.loads(mensaje_raw)
                tipo = mensaje.get("tipo", "")

                if tipo == "reiniciar":
                    # Detener el bucle actual
                    stop_event.set()
                    try:
                        await tarea_juego
                    except asyncio.CancelledError:
                        pass

                    # Guardar progreso antes de reiniciar
                    if controlador.mejor_cromosoma_historico:
                        guardar_mejor_cromosoma(
                            controlador.mejor_cromosoma_historico,
                            controlador.mejor_fitness_historico,
                        )

                    # Crear nuevo controlador y reiniciar el bucle
                    controlador = GAController()
                    stop_event = asyncio.Event()
                    tarea_juego = asyncio.create_task(
                        bucle_juego(controlador, enviar_estado, stop_event)
                    )

                elif tipo == "velocidad":
                    # Ajustar factor de velocidad de simulación (1×, 2×, 5×, 10×)
                    factor = int(mensaje.get("factor", 1))
                    controlador.factor_velocidad = max(1, min(20, factor))

                # "toggle_vista" es manejado completamente en el frontend

            except json.JSONDecodeError:
                pass  # Ignorar mensajes malformados silenciosamente

    except WebSocketDisconnect:
        pass  # Desconexión normal del cliente

    finally:
        # Detener el bucle del juego al cerrar la conexión
        stop_event.set()
        tarea_juego.cancel()
        try:
            await tarea_juego
        except (asyncio.CancelledError, Exception):
            pass

        # Persistir el mejor cromosoma de la sesión
        if controlador.mejor_cromosoma_historico:
            guardar_mejor_cromosoma(
                controlador.mejor_cromosoma_historico,
                controlador.mejor_fitness_historico,
            )
