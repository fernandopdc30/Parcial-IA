import json
import os

from backend.domain.value_objects.chromosome import Chromosome

# Ruta del archivo de persistencia (relativa al directorio de trabajo)
RUTA_ARCHIVO = "mejor_cromosoma.json"


def guardar_mejor_cromosoma(cromosoma: Chromosome, fitness: float) -> None:
    """
    Persiste el mejor cromosoma encontrado en un archivo JSON local.
    Sobrescribe el archivo si ya existe (siempre guarda el mejor de la sesión actual).

    Esto permite que sesiones futuras partan de un punto de referencia conocido,
    aunque el AG reinicia la población desde cero.

    Args:
        cromosoma: El mejor cromosoma a persistir
        fitness: El fitness que alcanzó este cromosoma (para referencia)
    """
    datos = {
        "umbral_distancia": cromosoma.umbral_distancia,
        "umbral_velocidad": cromosoma.umbral_velocidad,
        "fitness": fitness,
    }
    try:
        with open(RUTA_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    except OSError:
        # No interrumpir el juego si la escritura falla (entorno read-only, etc.)
        pass


def cargar_mejor_cromosoma() -> tuple[Chromosome, float] | None:
    """
    Carga el mejor cromosoma guardado desde el archivo JSON.

    Returns:
        Tupla (cromosoma, fitness) si existe y es válido el archivo,
        None si no existe o está corrupto
    """
    if not os.path.exists(RUTA_ARCHIVO):
        return None

    try:
        with open(RUTA_ARCHIVO, "r", encoding="utf-8") as f:
            datos = json.load(f)

        cromosoma = Chromosome(
            umbral_distancia=float(datos["umbral_distancia"]),
            umbral_velocidad=float(datos["umbral_velocidad"]),
        )
        return cromosoma, float(datos["fitness"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        # Archivo corrupto o formato incorrecto → ignorar
        return None
