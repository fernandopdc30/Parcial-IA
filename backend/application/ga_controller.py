import random

from backend.config import (
    AVATAR_X,
    OBSTACULO_INTERVALO_MAX,
    OBSTACULO_INTERVALO_MIN,
    SUELO_Y,
    TAMANO_POBLACION,
    VELOCIDAD_INICIAL,
)
from backend.domain.entities.avatar import Avatar
from backend.domain.entities.generation import Generation
from backend.domain.entities.obstacle import Obstacle
from backend.domain.use_cases.evaluate_fitness import evaluar_poblacion
from backend.domain.use_cases.evolve_population import (
    evolucionar,
    inicializar_poblacion,
)
from backend.domain.value_objects.chromosome import Chromosome


class GAController:
    """
    Controlador del Algoritmo Genético y del ciclo de vida de las generaciones.

    Responsabilidades:
    - Inicializar y reiniciar la población
    - Detectar el fin de una generación (todos muertos)
    - Invocar el AG para producir la siguiente generación
    - Mantener estadísticas: historial, mejor fitness, mejor cromosoma
    - Rastrear qué obstáculos han sido superados por los avatares vivos
    """

    def __init__(self):
        """Inicializa el controlador con la primera generación de avatares."""
        self.numero_generacion: int = 0
        self.poblacion: list[Avatar] = []
        self.obstaculos: list[Obstacle] = []
        self.velocidad_juego: float = VELOCIDAD_INICIAL
        self.frames_hasta_obstaculo: int = random.randint(
            OBSTACULO_INTERVALO_MIN, OBSTACULO_INTERVALO_MAX
        )
        self.historial_generaciones: list[Generation] = []
        self.mejor_fitness_historico: float = 0.0
        self.mejor_cromosoma_historico: Chromosome | None = None

        # Conjunto de ids de obstáculos ya contados como superados en esta generación
        self._obstaculos_contados: set[int] = set()

        # Factor de velocidad de simulación: 1=normal, 2=doble velocidad, etc.
        # El bucle del juego ejecuta este número de ticks físicos por frame visual
        self.factor_velocidad: int = 1

        # Arrancar la primera generación con cromosomas aleatorios
        self._nueva_generacion(inicializar_poblacion(TAMANO_POBLACION))

    # ------------------------------------------------------------------
    # Gestión interna de generaciones
    # ------------------------------------------------------------------

    def _nueva_generacion(self, cromosomas: list[Chromosome]) -> None:
        """
        Crea una nueva población de avatares a partir de una lista de cromosomas.
        Reinicia el estado del juego: obstáculos, velocidad y contador de intervalo.

        Args:
            cromosomas: Lista de cromosomas para los nuevos avatares
        """
        self.numero_generacion += 1
        self.obstaculos = []
        self.velocidad_juego = VELOCIDAD_INICIAL
        self.frames_hasta_obstaculo = random.randint(
            OBSTACULO_INTERVALO_MIN, OBSTACULO_INTERVALO_MAX
        )
        self._obstaculos_contados = set()

        # Crear un Avatar por cada cromosoma
        self.poblacion = [
            Avatar(
                id=i,
                cromosoma=cromosomas[i],
                x=float(AVATAR_X),
                y=float(SUELO_Y),
            )
            for i in range(len(cromosomas))
        ]

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------

    def todos_muertos(self) -> bool:
        """Retorna True si no queda ningún avatar vivo en la generación actual."""
        return all(not av.vivo for av in self.poblacion)

    def contar_vivos(self) -> int:
        """Cuenta y retorna el número de avatares actualmente vivos."""
        return sum(1 for av in self.poblacion if av.vivo)

    def obtener_mejor_actual(self) -> Avatar | None:
        """
        Retorna el avatar con mayor fitness en tiempo real.
        Para avatares vivos, calcula el fitness parcial sin marcarlos como muertos.

        Returns:
            El avatar de mayor fitness, o None si la población está vacía
        """
        if not self.poblacion:
            return None
        # Actualizar fitness parcial de avatares vivos (sin llamar calcular_fitness
        # que modificaría el estado; usamos asignación directa)
        for av in self.poblacion:
            if av.vivo:
                av.fitness = float(
                    av.frames_sobrevividos + av.obstaculos_superados * 50
                )
        return max(self.poblacion, key=lambda av: av.fitness)

    # ------------------------------------------------------------------
    # Conteo de obstáculos superados
    # ------------------------------------------------------------------

    def actualizar_obstaculos_superados(self) -> None:
        """
        Detecta qué obstáculos han pasado por delante de los avatares vivos
        e incrementa su contador de obstaculos_superados.

        Un obstáculo se considera superado cuando su borde derecho cruza
        el borde izquierdo del avatar (x borde derecho obs < AVATAR_X).
        Cada obstáculo se cuenta una sola vez por generación (uso de set de ids).
        """
        for obs in self.obstaculos:
            obs_id = id(obs)
            if obs_id not in self._obstaculos_contados:
                # El borde derecho del obstáculo pasó el borde izquierdo del avatar
                if obs.x + obs.ancho < AVATAR_X:
                    self._obstaculos_contados.add(obs_id)
                    for av in self.poblacion:
                        if av.vivo:
                            av.obstaculos_superados += 1

    # ------------------------------------------------------------------
    # Evolución entre generaciones
    # ------------------------------------------------------------------

    def evolucionar_generacion(self) -> None:
        """
        Evalúa el fitness de la población actual, registra estadísticas y
        aplica el AG para producir la siguiente generación de cromosomas.

        Proceso:
          1. Asegurar que todos los avatares tengan fitness calculado
          2. Registrar estadísticas en el historial de generaciones
          3. Actualizar el mejor cromosoma histórico si corresponde
          4. Aplicar el AG (selección, crossover, mutación, elitismo)
          5. Iniciar la nueva generación con los nuevos cromosomas
        """
        # 1. Calcular fitness final de todos los avatares
        evaluar_poblacion(self.poblacion)

        # Identificar el mejor individuo de esta generación
        mejor_avatar = max(self.poblacion, key=lambda av: av.fitness)
        fitnesses = [av.fitness for av in self.poblacion]

        # 2. Registrar estadísticas de la generación que termina
        gen_stats = Generation(
            numero=self.numero_generacion,
            mejor_fitness=mejor_avatar.fitness,
            fitness_promedio=sum(fitnesses) / len(fitnesses) if fitnesses else 0.0,
            mejor_cromosoma_distancia=mejor_avatar.cromosoma.umbral_distancia,
            mejor_cromosoma_velocidad=mejor_avatar.cromosoma.umbral_velocidad,
        )
        self.historial_generaciones.append(gen_stats)

        # 3. Actualizar mejor fitness e cromosoma histórico
        if mejor_avatar.fitness > self.mejor_fitness_historico:
            self.mejor_fitness_historico = mejor_avatar.fitness
            self.mejor_cromosoma_historico = mejor_avatar.cromosoma

        # 4. Aplicar el AG para obtener los cromosomas de la siguiente generación
        nuevos_cromosomas = evolucionar(self.poblacion)

        # 5. Iniciar la nueva generación
        self._nueva_generacion(nuevos_cromosomas)

    # ------------------------------------------------------------------
    # Serialización de estadísticas para el HUD
    # ------------------------------------------------------------------

    def obtener_stats(self) -> dict:
        """
        Construye y retorna el diccionario de estadísticas para enviar al cliente.
        Incluye datos de la generación actual y el historial de las últimas 20.

        Returns:
            Diccionario JSON-serializable con todos los campos del HUD
        """
        mejor_actual = self.obtener_mejor_actual()
        mejor_fitness_actual = mejor_actual.fitness if mejor_actual else 0.0

        # Usar el mejor cromosoma histórico si existe, si no el actual
        mejor_crom = (
            self.mejor_cromosoma_historico
            if self.mejor_cromosoma_historico
            else (mejor_actual.cromosoma if mejor_actual else None)
        )

        # Últimas 20 generaciones para el gráfico
        historial_fitness = [g.mejor_fitness for g in self.historial_generaciones[-20:]]

        return {
            "generacion": self.numero_generacion,
            "vivos": self.contar_vivos(),
            "mejor_fitness_actual": round(mejor_fitness_actual, 1),
            "mejor_fitness_historico": round(self.mejor_fitness_historico, 1),
            "mejor_cromosoma": (
                [
                    round(mejor_crom.umbral_distancia, 1),
                    round(mejor_crom.umbral_velocidad, 2),
                ]
                if mejor_crom
                else [0.0, 0.0]
            ),
            "historial_fitness": historial_fitness,
        }
