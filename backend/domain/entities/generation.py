from dataclasses import dataclass


@dataclass
class Generation:
    """
    Entidad que agrupa los datos estadísticos de una generación completada.
    Se crea al finalizar una generación y se utiliza para construir el historial
    de fitness que se muestra en el gráfico del HUD.
    """

    numero: int  # Número de generación (comienza en 1)
    mejor_fitness: float = 0.0  # Mejor fitness alcanzado en esta generación
    fitness_promedio: float = 0.0  # Fitness promedio de toda la población
    mejor_cromosoma_distancia: float = 0.0  # Gen umbral_distancia del mejor individuo
    mejor_cromosoma_velocidad: float = 0.0  # Gen umbral_velocidad del mejor individuo
