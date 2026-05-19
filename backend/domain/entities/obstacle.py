from dataclasses import dataclass


@dataclass
class Obstacle:
    """
    Entidad que representa un obstáculo en el juego.
    Se mueve de derecha a izquierda a la velocidad actual del juego.
    La posición (x, y) corresponde a la esquina superior-izquierda del rectángulo.
    """

    x: float  # Posición horizontal (decrece cada frame al moverse hacia la izquierda)
    y: float  # Posición vertical (esquina superior; el obstáculo descansa sobre el suelo)
    ancho: float  # Ancho del obstáculo en píxeles
    alto: float  # Alto del obstáculo en píxeles

    def mover(self, velocidad: float) -> None:
        """
        Desplaza el obstáculo hacia la izquierda según la velocidad del juego.

        Args:
            velocidad: Número de píxeles a desplazar hacia la izquierda por frame
        """
        self.x -= velocidad

    def esta_fuera_de_pantalla(self) -> bool:
        """
        Retorna True si el obstáculo salió completamente por el borde izquierdo del canvas.
        Esto indica que debe ser eliminado de la lista de obstáculos activos.
        """
        return self.x + self.ancho < 0
