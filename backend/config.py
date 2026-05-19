# ===========================
# config.py — Dino Runner GA
# Todos los parámetros del juego y del AG en un único lugar.
# NINGÚN número mágico debe aparecer fuera de este archivo.
# ===========================

# ---- Parámetros del Algoritmo Genético ----
TAMANO_POBLACION = 30  # Número de individuos por generación
ELITISMO = 2  # Cantidad de mejores individuos que pasan sin cambios
TORNEO_K = 3  # Tamaño del torneo de selección
PROB_CROSSOVER = 0.8  # Probabilidad de que ocurra crossover entre dos padres
PROB_MUTACION = 0.1  # Probabilidad de mutación por gen
SIGMA_MUTACION = 20.0  # Desviación estándar de la perturbación gaussiana

# ---- Parámetros físicos del juego ----
VELOCIDAD_INICIAL = 4.0  # Velocidad de desplazamiento al inicio de cada generación
INCREMENTO_VELOCIDAD = (
    0.001  # Incremento de velocidad por frame (el juego acelera gradualmente)
)
GRAVEDAD = 0.6  # Aceleración vertical hacia abajo (px/frame²)
VELOCIDAD_SALTO = -12.0  # Impulso vertical inicial al saltar (negativo = hacia arriba)

# ---- Geometría del canvas ----
ANCHO_CANVAS = 800  # Ancho del canvas en píxeles
ALTO_CANVAS = 400  # Alto del canvas en píxeles
SUELO_Y = 340  # Coordenada Y del suelo (los avatares descansan aquí)

# ---- Geometría de los avatares ----
AVATAR_X = 80  # Posición X fija de todos los avatares (columna izquierda)
AVATAR_ANCHO = 20  # Ancho del bounding box del avatar en píxeles
AVATAR_ALTO = 40  # Alto del bounding box del avatar en píxeles

# ---- Geometría de los obstáculos ----
OBSTACULO_MIN_ANCHO = 20  # Ancho mínimo de un obstáculo en píxeles
OBSTACULO_MAX_ANCHO = 40  # Ancho máximo de un obstáculo en píxeles
OBSTACULO_MIN_ALTO = 30  # Alto mínimo de un obstáculo en píxeles
OBSTACULO_MAX_ALTO = 70  # Alto máximo de un obstáculo en píxeles

# ---- Intervalos de generación de obstáculos ----
OBSTACULO_INTERVALO_MIN = 60  # Mínimo de frames entre la aparición de obstáculos
OBSTACULO_INTERVALO_MAX = 120  # Máximo de frames entre la aparición de obstáculos

# ---- Límites del cromosoma ----
UMBRAL_DISTANCIA_MIN = 50.0  # Valor mínimo del gen umbral_distancia
UMBRAL_DISTANCIA_MAX = 400.0  # Valor máximo del gen umbral_distancia
UMBRAL_VELOCIDAD_MIN = 0.0  # Valor mínimo del gen umbral_velocidad
UMBRAL_VELOCIDAD_MAX = 20.0  # Valor máximo del gen umbral_velocidad

# ---- Control de tiempo ----
FPS_OBJETIVO = 60  # Frames por segundo objetivo del bucle del juego
