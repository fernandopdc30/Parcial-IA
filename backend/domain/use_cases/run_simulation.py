import random
from typing import Optional

from backend.config import (
    ANCHO_CANVAS,
    AVATAR_ALTO,
    AVATAR_ANCHO,
    AVATAR_X,
    GRAVEDAD,
    INCREMENTO_VELOCIDAD,
    OBSTACULO_INTERVALO_MAX,
    OBSTACULO_INTERVALO_MIN,
    OBSTACULO_MAX_ALTO,
    OBSTACULO_MAX_ANCHO,
    OBSTACULO_MIN_ALTO,
    OBSTACULO_MIN_ANCHO,
    SUELO_Y,
    VELOCIDAD_SALTO,
)
from backend.domain.entities.avatar import Avatar
from backend.domain.entities.obstacle import Obstacle


def decidir_salto(
    avatar: Avatar,
    obstaculos: list[Obstacle],
    velocidad_juego: float,
) -> bool:
    """
    Evalúa si el avatar debe iniciar un salto según su cromosoma.

    Regla de decisión:
        si (distancia_al_obstáculo_más_cercano < umbral_distancia
            Y velocidad_juego > umbral_velocidad):
            → saltar

    Solo puede saltar si está en el suelo (no se permiten saltos dobles).

    Args:
        avatar: El avatar que toma la decisión
        obstaculos: Lista de obstáculos activos en pantalla
        velocidad_juego: Velocidad actual del desplazamiento del juego

    Returns:
        True si el avatar debe intentar saltar, False en caso contrario
    """
    if not avatar.en_suelo:
        return False  # No puede saltar si ya está en el aire

    # Encontrar el obstáculo más cercano que esté delante del avatar
    distancia_minima = float("inf")
    hay_obstaculo = False

    for obs in obstaculos:
        if obs.x > avatar.x:  # Solo obstáculos por delante del avatar
            # Distancia desde el borde derecho del avatar hasta el borde izquierdo del obstáculo
            distancia = obs.x - (avatar.x + AVATAR_ANCHO)
            if distancia < distancia_minima:
                distancia_minima = distancia
                hay_obstaculo = True

    if not hay_obstaculo:
        return False  # No hay obstáculos por delante

    # Aplicar la regla del cromosoma
    return (
        distancia_minima < avatar.cromosoma.umbral_distancia
        and velocidad_juego > avatar.cromosoma.umbral_velocidad
    )


def hacer_saltar(avatar: Avatar) -> None:
    """
    Aplica el impulso de salto al avatar si está en el suelo.
    Modifica el estado del avatar in-place.

    Args:
        avatar: Avatar al que se aplica el salto
    """
    if avatar.en_suelo and avatar.vivo:
        avatar.velocidad_y = VELOCIDAD_SALTO
        avatar.en_suelo = False


def actualizar_avatar(avatar: Avatar) -> None:
    """
    Aplica física (gravedad, movimiento vertical, detección de suelo) a un avatar vivo.
    Modifica el estado del avatar in-place.

    Args:
        avatar: Avatar a actualizar (no hace nada si está muerto)
    """
    if not avatar.vivo:
        return

    # Aplicar gravedad: incrementa velocidad hacia abajo cada frame
    avatar.velocidad_y += GRAVEDAD
    avatar.y += avatar.velocidad_y

    # Detectar aterrizaje en el suelo
    if avatar.y >= SUELO_Y:
        avatar.y = SUELO_Y
        avatar.velocidad_y = 0.0
        avatar.en_suelo = True
    else:
        avatar.en_suelo = False

    # Incrementar contador de supervivencia
    avatar.frames_sobrevividos += 1


def detectar_colision(avatar: Avatar, obstaculo: Obstacle) -> bool:
    """
    Detecta colisión rectangular entre un avatar y un obstáculo.
    Usa AABB (Axis-Aligned Bounding Box) para simplicidad y rendimiento.

    Coordenadas del avatar:
        izquierda = avatar.x
        derecha   = avatar.x + AVATAR_ANCHO
        arriba    = avatar.y - AVATAR_ALTO  (avatar.y es la BASE)
        abajo     = avatar.y

    Args:
        avatar: El avatar a verificar
        obstaculo: El obstáculo contra el que se comprueba

    Returns:
        True si los bounding boxes se solapan (colisión), False en caso contrario
    """
    # Bounding box del avatar (avatar.y es la base → parte inferior)
    av_izq = avatar.x
    av_der = avatar.x + AVATAR_ANCHO
    av_arr = avatar.y - AVATAR_ALTO
    av_aba = avatar.y

    # Bounding box del obstáculo (obstaculo.y es la esquina superior)
    obs_izq = obstaculo.x
    obs_der = obstaculo.x + obstaculo.ancho
    obs_arr = obstaculo.y
    obs_aba = obstaculo.y + obstaculo.alto

    # Solapamiento en ambos ejes = colisión
    return (
        av_der > obs_izq and av_izq < obs_der and av_aba > obs_arr and av_arr < obs_aba
    )


def generar_obstaculo(velocidad_juego: float) -> Obstacle:
    """
    Genera un nuevo obstáculo con dimensiones aleatorias en el borde derecho del canvas.
    El obstáculo descansa sobre el suelo (su base está en SUELO_Y).

    Args:
        velocidad_juego: Velocidad actual del juego (parámetro disponible para
                         extensiones futuras como dificultad adaptativa)

    Returns:
        Nuevo obstáculo listo para ser añadido a la lista de obstáculos activos
    """
    ancho = random.uniform(OBSTACULO_MIN_ANCHO, OBSTACULO_MAX_ANCHO)
    alto = random.uniform(OBSTACULO_MIN_ALTO, OBSTACULO_MAX_ALTO)
    # El obstáculo aparece justo fuera del borde derecho del canvas
    x = float(ANCHO_CANVAS + 2)
    # El obstáculo descansa sobre el suelo: su esquina superior = SUELO_Y - alto
    y = float(SUELO_Y - alto)
    return Obstacle(x=x, y=y, ancho=float(ancho), alto=float(alto))


def tick_simulacion(
    avatares: list[Avatar],
    obstaculos: list[Obstacle],
    velocidad_juego: float,
    frames_hasta_obstaculo: int,
) -> tuple[list[Obstacle], float, int]:
    """
    Ejecuta un tick (frame) completo de la simulación física del juego.

    Orden de operaciones por tick:
      1. Incrementar velocidad del juego gradualmente
      2. Para cada avatar vivo: decidir salto, actualizar física, detectar colisiones
      3. Mover todos los obstáculos hacia la izquierda
      4. Eliminar obstáculos que salieron de pantalla
      5. Generar nuevo obstáculo si el contador llegó a 0

    Nota: el conteo de obstáculos superados se delega al GAController para
    poder identificar correctamente cada obstáculo entre ticks.

    Args:
        avatares: Lista de todos los avatares (vivos y muertos se incluyen)
        obstaculos: Lista de obstáculos activos en pantalla
        velocidad_juego: Velocidad actual del desplazamiento horizontal
        frames_hasta_obstaculo: Frames restantes hasta generar el próximo obstáculo

    Returns:
        Tupla (lista_obstaculos_actualizada, nueva_velocidad, nuevo_contador_frames)
    """
    # 1. Incrementar velocidad del juego gradualmente (el juego se vuelve más difícil)
    velocidad_juego += INCREMENTO_VELOCIDAD

    # 2. Actualizar cada avatar vivo
    for avatar in avatares:
        if not avatar.vivo:
            continue

        # Decidir si el avatar debe saltar (según su cromosoma)
        if decidir_salto(avatar, obstaculos, velocidad_juego):
            hacer_saltar(avatar)

        # Aplicar física (gravedad, posición vertical, aterrizaje)
        actualizar_avatar(avatar)

        # Detectar colisiones con todos los obstáculos activos
        for obs in obstaculos:
            if detectar_colision(avatar, obs):
                avatar.vivo = False
                avatar.calcular_fitness()
                break  # Un avatar solo puede morir una vez por tick

    # 3. Mover todos los obstáculos hacia la izquierda
    for obs in obstaculos:
        obs.mover(velocidad_juego)

    # 4. Eliminar obstáculos que ya salieron completamente de la pantalla
    obstaculos_activos = [obs for obs in obstaculos if not obs.esta_fuera_de_pantalla()]

    # 5. Generar nuevo obstáculo cuando el contador llega a 0
    frames_hasta_obstaculo -= 1
    if frames_hasta_obstaculo <= 0:
        nuevo_obs = generar_obstaculo(velocidad_juego)
        obstaculos_activos.append(nuevo_obs)
        # Reiniciar contador con intervalo aleatorio
        frames_hasta_obstaculo = random.randint(
            OBSTACULO_INTERVALO_MIN, OBSTACULO_INTERVALO_MAX
        )

    return obstaculos_activos, velocidad_juego, frames_hasta_obstaculo
