"""
main.py — Punto de entrada de la aplicación Dino Runner GA.

Configura la aplicación FastAPI:
  - GET /         → sirve index.html del frontend
  - WS  /ws       → endpoint WebSocket del juego
  - GET /static/* → archivos estáticos del frontend (CSS, JS)
"""

import os

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.infrastructure.websocket_server import manejar_websocket

# Crear la aplicación FastAPI con metadatos
app = FastAPI(
    title="Dino Runner GA",
    description="Juego de evolución con Algoritmo Genético — avatares aprenden a saltar obstáculos",
    version="1.0.0",
)

# Calcular rutas absolutas de forma independiente del directorio de trabajo
_RUTA_ESTE_ARCHIVO = os.path.abspath(__file__)  # .../backend/main.py
_RUTA_RAIZ = os.path.dirname(os.path.dirname(_RUTA_ESTE_ARCHIVO))  # raíz del proyecto
RUTA_FRONTEND = os.path.join(_RUTA_RAIZ, "frontend")


@app.get("/", include_in_schema=False)
async def servir_index() -> FileResponse:
    """
    Sirve la página principal del juego.
    El frontend carga sus recursos (/static/style.css, /static/game.js)
    desde el servidor estático montado más abajo.
    """
    return FileResponse(os.path.join(RUTA_FRONTEND, "index.html"))


@app.websocket("/ws")
async def endpoint_websocket(websocket: WebSocket) -> None:
    """
    Endpoint WebSocket principal del juego.
    Delega toda la lógica de la sesión a la capa de infraestructura.
    """
    await manejar_websocket(websocket)


# Montar archivos estáticos del frontend en /static
# DEBE ir después de las rutas específicas para evitar que capture "/"
app.mount(
    "/static",
    StaticFiles(directory=RUTA_FRONTEND),
    name="static",
)


# Permitir ejecutar directamente: python -m backend.main
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
