from backend.domain.entities.avatar import Avatar


def evaluar_fitness(avatar: Avatar) -> float:
    """
    Caso de uso puro: calcula el fitness de un avatar en el momento de su muerte
    o al final de la generación.

    Fórmula: fitness = frames_sobrevividos + (obstaculos_superados * 50)

    La bonificación de 50 por obstáculo incentiva al AG a desarrollar avatares
    que superen obstáculos en lugar de simplemente sobrevivir parados.
    El valor 50 es deliberado: superar 1 obstáculo vale más que sobrevivir ~50 frames
    sin hacer nada (los obstáculos aparecen cada 60-120 frames).

    Args:
        avatar: El avatar cuyo fitness se calcula

    Returns:
        El valor de fitness calculado (también almacenado en avatar.fitness)
    """
    return avatar.calcular_fitness()


def evaluar_poblacion(poblacion: list[Avatar]) -> None:
    """
    Evalúa el fitness de todos los avatares en la población.
    Función pura que modifica únicamente el campo `fitness` de cada avatar.

    Args:
        poblacion: Lista de todos los avatares de la generación actual
    """
    for avatar in poblacion:
        evaluar_fitness(avatar)
