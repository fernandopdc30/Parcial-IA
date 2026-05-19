# 🦕 Dino Runner GA

Un juego de navegador donde una población de 30 avatares evoluciona usando un **Algoritmo Genético (AG)** para aprender a saltar obstáculos. Toda la lógica del AG y la física del juego corren en Python (FastAPI), y el navegador solo recibe el estado por WebSocket y lo dibuja en Canvas.

---

## 📸 Vista previa

*(Captura o GIF del juego en funcionamiento)*

---

## 🏗️ Arquitectura (Clean Architecture)

```
Navegador (Canvas + JS)  ←── WebSocket JSON ──→  FastAPI (Python)
                                                        │
                                             ┌──────────▼──────────┐
                                             │  GAController        │
                                             │  (application/)      │
                                             └──────────┬──────────┘
                                                        │
                                             ┌──────────▼──────────┐
                                             │  Domain Layer        │
                                             │  ├─ entities/        │
                                             │  ├─ use_cases/       │
                                             │  └─ value_objects/   │
                                             └─────────────────────┘
```

| Capa | Responsabilidad | Dependencias externas |
|---|---|---|
| **domain** | Lógica pura del juego y del AG | Solo numpy |
| **application** | Bucle de juego asyncio, ciclo de generaciones | domain |
| **infrastructure** | WebSocket FastAPI, persistencia JSON | fastapi, websockets |
| **frontend** | Renderizado Canvas, HUD, botones | Ninguna (JS vanilla) |

---

## 🚀 Instalación y ejecución local

### Requisitos
- Python 3.11+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd dino-runner-ga

# 2. (Opcional) Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar el servidor
uvicorn backend.main:app --reload

# 5. Abrir el juego en el navegador
#    http://localhost:8000
```

---

## 🌐 Despliegue en producción gratuita

### Opción A — Railway

1. Crea una cuenta en [railway.app](https://railway.app)
2. Nuevo proyecto → **Deploy from GitHub repo**
3. Conecta tu repositorio
4. En **Settings → Start Command**:
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
5. Railway detecta automáticamente `requirements.txt` y `Python`

### Opción B — Render

1. Crea una cuenta en [render.com](https://render.com)
2. Nuevo servicio → **Web Service** → conecta tu repositorio
3. Configura:
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Render asigna automáticamente `$PORT`

> **WebSockets en producción**: El cliente detecta automáticamente si usar `ws://` o `wss://` según el protocolo HTTPS, sin cambios de código.

---

## 🧬 Parámetros del Algoritmo Genético

Todos los parámetros viven en `backend/config.py`:

| Parámetro | Valor | Descripción |
|---|---|---|
| `TAMANO_POBLACION` | 30 | Individuos por generación |
| `ELITISMO` | 2 | Mejores que pasan sin cambios |
| `TORNEO_K` | 3 | Tamaño del torneo de selección |
| `PROB_CROSSOVER` | 0.8 | Probabilidad de crossover |
| `PROB_MUTACION` | 0.1 | Probabilidad de mutación por gen |
| `SIGMA_MUTACION` | 20.0 | Desviación estándar gaussiana |
| `VELOCIDAD_INICIAL` | 4.0 | Velocidad al inicio de cada generación |
| `INCREMENTO_VELOCIDAD` | 0.001 | Aceleración progresiva del juego |

## 🧬 Cromosoma

Cada avatar tiene dos genes de valor real:

| Gen | Rango | Significado |
|---|---|---|
| `umbral_distancia` | [50, 400] | Distancia al obstáculo para considerar saltar |
| `umbral_velocidad` | [0, 20] | Velocidad mínima del juego para saltar |

**Regla de salto**: `si distancia < umbral_distancia Y velocidad > umbral_velocidad → saltar`

---

## 🎮 Controles

| Control | Acción |
|---|---|
| 🔄 Reiniciar Evolución | Reinicia el AG desde cero |
| 👁 Solo el Mejor / Mostrar Todos | Alterna visibilidad de la población |

---

## 📁 Estructura del proyecto

```
dino-runner-ga/
├── backend/
│   ├── domain/
│   │   ├── entities/          # Avatar, Obstacle, Generation
│   │   ├── value_objects/     # Chromosome (frozen dataclass)
│   │   └── use_cases/         # evolve_population, evaluate_fitness, run_simulation
│   ├── application/
│   │   ├── game_loop.py       # Bucle asyncio a 60 FPS
│   │   └── ga_controller.py   # Ciclo de vida de generaciones
│   ├── infrastructure/
│   │   ├── websocket_server.py
│   │   └── best_chromosome_storage.py
│   ├── config.py              # Todos los parámetros (sin números mágicos en el código)
│   └── main.py                # FastAPI app
├── frontend/
│   ├── index.html             # Layout Canvas + HUD
│   ├── game.js                # WebSocket + renderizado + gráfico
│   └── style.css              # Tema oscuro responsive
├── requirements.txt
├── README.md
└── DOCUMENTACION.md
```

---

## 📄 Licencia

MIT
