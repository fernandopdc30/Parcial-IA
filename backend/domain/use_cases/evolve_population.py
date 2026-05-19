import random

import numpy as np

from backend.config import (
    ELITISMO,
    PROB_CROSSOVER,
    PROB_MUTACION,
    SIGMA_MUTACION,
    TAMANO_POBLACION,
    TORNEO_K,
    UMBRAL_DISTANCIA_MAX,
    UMBRAL_DISTANCIA_MIN,
    UMBRAL_VELOCIDAD_MAX,
    UMBRAL_VELOCIDAD_MIN,
)
from backend.domain.entities.avatar import Avatar
from backend.domain.value_objects.chromosome import Chromosome


def inicializar_poblacion(n: int) -> list[Chromosome]:
    """
    Crea una población inicial con cromosomas aleatorios uniformes dentro de los límites.

    La distribución uniforme garantiza exploración completa del espacio de búsqueda
    al inicio, sin sesgo hacia ninguna región. No se asume conocimiento previo
    sobre qué valores de umbral son mejores.

    Args:
        n: Número de individuos en la población

    Returns:
        Lista de n cromosomas con valores aleatorios uniformes
    """
    cromosomas = []
    for _ in range(n):
        distancia = float(np.random.uniform(UMBRAL_DISTANCIA_MIN, UMBRAL_DISTANCIA_MAX))
        velocidad = float(np.random.uniform(UMBRAL_VELOCIDAD_MIN, UMBRAL_VELOCIDAD_MAX))
        cromosomas.append(
            Chromosome(
                umbral_distancia=distancia,
                umbral_velocidad=velocidad,
            )
        )
    return cromosomas


def seleccion_torneo(poblacion: list[Avatar], k: int) -> Avatar:
    """
    Selección por torneo: elige k individuos al azar y retorna el de mayor fitness.

    El torneo con k=3 ofrece mejor balance entre presión selectiva y diversidad que:
    - Ruleta: puede perder diversidad si hay fitnesses muy dispares (un individuo
      domina toda la distribución)
    - Ranking: presión selectiva constante pero pierde información de magnitud

    Con k=3, incluso individuos de fitness mediocre tienen oportunidad de reproducirse,
    manteniendo la diversidad genética de la población.

    Args:
        poblacion: Lista de avatares con fitness calculado
        k: Tamaño del torneo (número de competidores seleccionados al azar)

    Returns:
        El avatar con mayor fitness dentro del grupo de k candidatos
    """
    # Seleccionar k candidatos aleatorios (sin reemplazo)
    candidatos = random.sample(poblacion, min(k, len(poblacion)))
    # Retornar el ganador: el de mayor fitness
    return max(candidatos, key=lambda a: a.fitness)


def crossover_un_punto(
    padre1: Chromosome,
    padre2: Chromosome,
    pc: float,
) -> tuple[Chromosome, Chromosome]:
    """
    Crossover de un punto para cromosomas de 2 genes.

    Con probabilidad pc intercambia los genes en el punto de corte.
    Para cromosomas de 2 genes, existe un único punto de corte (entre gen 0 y gen 1),
    lo que equivale a intercambiar un gen entre los padres.

    Ejemplo:
        padre1 = [dist=200, vel=5]
        padre2 = [dist=100, vel=8]
        → hijo1 = [dist=200, vel=8]   (gen 0 de padre1, gen 1 de padre2)
        → hijo2 = [dist=100, vel=5]   (gen 0 de padre2, gen 1 de padre1)

    Args:
        padre1: Cromosoma del primer padre
        padre2: Cromosoma del segundo padre
        pc: Probabilidad de que ocurra el crossover (si no ocurre, hijos = padres)

    Returns:
        Tupla (hijo1, hijo2) con los cromosomas resultantes
    """
    if np.random.random() < pc:
        # Crossover en el único punto posible para 2 genes: entre gen 0 y gen 1
        hijo1 = Chromosome(
            umbral_distancia=padre1.umbral_distancia,
            umbral_velocidad=padre2.umbral_velocidad,
        )
        hijo2 = Chromosome(
            umbral_distancia=padre2.umbral_distancia,
            umbral_velocidad=padre1.umbral_velocidad,
        )
        return hijo1, hijo2
    else:
        # Sin crossover: los hijos son copias exactas de los padres
        return padre1, padre2


def mutacion_gaussiana(
    cromosoma: Chromosome,
    pm: float,
    sigma: float,
) -> Chromosome:
    """
    Mutación gaussiana: para cada gen, con probabilidad pm suma ruido N(0, sigma).

    La mutación gaussiana es la elección canónica para espacios continuos porque:
    - Introduce perturbaciones pequeñas con alta probabilidad (exploración local)
    - Permite cambios grandes ocasionales con baja probabilidad (escapar óptimos locales)
    - El bit-flip en espacios continuos haría saltos arbitrariamente grandes

    El valor de sigma para velocidad se escala proporcionalmente al rango del gen
    para evitar perturbaciones desproporcionadas.

    Args:
        cromosoma: Cromosoma a (posiblemente) mutar
        pm: Probabilidad de mutación por gen (independiente para cada gen)
        sigma: Desviación estándar del ruido gaussiano para umbral_distancia

    Returns:
        Nuevo cromosoma (puede ser igual al original si ningún gen mutó)
        con valores garantizados dentro de los límites del cromosoma
    """
    distancia = cromosoma.umbral_distancia
    velocidad = cromosoma.umbral_velocidad

    # Mutar gen umbral_distancia (rango [50, 400], sigma proporcional)
    if np.random.random() < pm:
        distancia += float(np.random.normal(0.0, sigma))
        distancia = float(
            np.clip(distancia, UMBRAL_DISTANCIA_MIN, UMBRAL_DISTANCIA_MAX)
        )

    # Mutar gen umbral_velocidad (rango [0, 20], sigma escalado al 10% del sigma principal)
    if np.random.random() < pm:
        sigma_vel = sigma * (UMBRAL_VELOCIDAD_MAX / UMBRAL_DISTANCIA_MAX)  # ~1.0
        velocidad += float(np.random.normal(0.0, sigma_vel))
        velocidad = float(
            np.clip(velocidad, UMBRAL_VELOCIDAD_MIN, UMBRAL_VELOCIDAD_MAX)
        )

    return Chromosome(umbral_distancia=distancia, umbral_velocidad=velocidad)


def evolucionar(poblacion: list[Avatar]) -> list[Chromosome]:
    """
    Función principal del AG: genera la siguiente generación de cromosomas.

    Algoritmo:
      1. Ordena la población por fitness descendente
      2. Conserva los ELITISMO mejores individuos sin cambios (intensificación)
      3. Rellena el resto mediante selección por torneo + crossover + mutación (exploración)

    El elitismo garantiza que las mejores soluciones nunca se degraden entre generaciones,
    implementando una forma de intensificación de la búsqueda.

    Args:
        poblacion: Lista de avatares con fitness ya calculado

    Returns:
        Lista de TAMANO_POBLACION nuevos cromosomas para la siguiente generación
    """
    # 1. Ordenar por fitness descendente (mejor primero)
    poblacion_ordenada = sorted(poblacion, key=lambda a: a.fitness, reverse=True)

    nuevos_cromosomas: list[Chromosome] = []

    # 2. Elitismo: copiar los mejores ELITISMO individuos sin modificación
    for i in range(min(ELITISMO, len(poblacion_ordenada))):
        nuevos_cromosomas.append(poblacion_ordenada[i].cromosoma)

    # 3. Completar el resto de la población
    while len(nuevos_cromosomas) < TAMANO_POBLACION:
        # Seleccionar dos padres por torneo
        padre1_av = seleccion_torneo(poblacion_ordenada, TORNEO_K)
        padre2_av = seleccion_torneo(poblacion_ordenada, TORNEO_K)

        # Crossover de un punto → dos hijos
        hijo1_crom, hijo2_crom = crossover_un_punto(
            padre1_av.cromosoma,
            padre2_av.cromosoma,
            PROB_CROSSOVER,
        )

        # Mutación gaussiana sobre cada hijo
        hijo1_crom = mutacion_gaussiana(hijo1_crom, PROB_MUTACION, SIGMA_MUTACION)
        hijo2_crom = mutacion_gaussiana(hijo2_crom, PROB_MUTACION, SIGMA_MUTACION)

        nuevos_cromosomas.append(hijo1_crom)
        if len(nuevos_cromosomas) < TAMANO_POBLACION:
            nuevos_cromosomas.append(hijo2_crom)

    # Retornar exactamente TAMANO_POBLACION cromosomas
    return nuevos_cromosomas[:TAMANO_POBLACION]
