from dataclasses import dataclass, field

from backend.domain.value_objects.chromosome import Chromosome


@dataclass
class Avatar:
    """
    Entidad que representa a un individuo de la población.
    Contiene su cromosoma (estrategia de salto), estado físico y métricas de fitness.
    """

    id: int  # Identificador único del avatar en la generación
    cromosoma: Chromosome  # Genes que determinan cuándo salta

    # Estado físico (se actualiza cada frame)
    x: float = 80.0  # Posición X (fija, los obstáculos se mueven hacia el avatar)
    y: float = 340.0  # Posición Y (base del bounding box; cambia al saltar)
    velocidad_y: float = 0.0  # Velocidad vertical actual (positivo = caída)
    vivo: bool = True  # False cuando choca con un obstáculo
    en_suelo: bool = True  # True cuando los pies tocan el suelo

    # Métricas de desempeño
    frames_sobrevividos: int = 0  # Cuántos ticks lleva vivo en esta generación
    obstaculos_superados: int = 0  # Cuántos obstáculos ha pasado sin colisionar
    fitness: float = 0.0  # Puntuación calculada (se actualiza al morir o al final)

    def calcular_fitness(self) -> float:
        """
        Calcula y almacena el fitness del avatar.
        Fórmula: fitness = frames_sobrevividos + obstaculos_superados * 50

        El factor 50 por obstáculo incentiva al AG a desarrollar avatares que
        realmente superen obstáculos en lugar de simplemente sobrevivir parados.

        Returns:
            El valor de fitness calculado (también almacenado en self.fitness)
        """
        self.fitness = float(self.frames_sobrevividos + self.obstaculos_superados * 50)
        return self.fitness
