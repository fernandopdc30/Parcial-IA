from dataclasses import dataclass


@dataclass(frozen=True)
class Chromosome:
    """
    Value Object inmutable que representa el cromosoma de un avatar.
    Contiene dos genes que definen la estrategia de salto:
      - umbral_distancia: distancia al obstáculo a partir de la cual el avatar considera saltar
      - umbral_velocidad: velocidad mínima del juego para que el avatar salte
    Ambos valores son flotantes continuos.
    """

    umbral_distancia: float  # ∈ [50, 400]
    umbral_velocidad: float  # ∈ [0, 20]
