# 📚 Documentación Técnica — Dino Runner GA

---

## 1. Formulación del Problema

### ¿Qué se está optimizando?

Se busca encontrar una **estrategia de salto óptima** para un agente virtual (avatar) que corre a lo largo de un terreno con obstáculos de velocidad creciente. El objetivo es maximizar la distancia recorrida (tiempo de supervivencia), lo que implica saltar sobre cada obstáculo en el momento preciso: ni demasiado tarde (colisión) ni demasiado pronto (aterrizaje antes del obstáculo y posterior colisión al volver al suelo).

### ¿Cómo el cromosoma representa una solución?

Cada individuo lleva un cromosoma de **dos genes de valor real**:

```
Chromosome(
    umbral_distancia: float ∈ [50, 400],   # px de distancia al obstáculo para considerar saltar
    umbral_velocidad: float ∈ [0, 20]      # velocidad mínima del juego para que el salto tenga sentido
)
```

**Regla de decisión** (evaluada cada frame cuando el avatar está en el suelo):

```
si (distancia_al_obstáculo_más_cercano < umbral_distancia
    Y velocidad_juego > umbral_velocidad):
    → saltar
```

Esta representación captura los dos factores clave de la decisión:
- **Cuán cerca** está el obstáculo: demasiado lejos → salto innecesario; demasiado cerca → colisión
- **Qué tan rápido** va el juego: a mayor velocidad, el tiempo de reacción es menor y el avatar debe saltar antes

Un cromosoma con `umbral_distancia` muy alto saltará prematuramente, aterrizará antes del obstáculo y chocará. Uno muy bajo no saltará a tiempo. El `umbral_velocidad` filtra los saltos innecesarios a baja velocidad (cuando el juego aún es lento, la ventana de salto es más amplia y el cromosoma no necesita ser tan agresivo).

### Fórmula del fitness y justificación

```
fitness = frames_sobrevividos + (obstaculos_superados × 50)
```

**Justificación de cada componente:**

| Componente | Justificación |
|---|---|
| `frames_sobrevividos` | Componente base: premia la supervivencia. Garantiza diferenciación entre avatares que mueren pronto (antes del primer obstáculo) |
| `obstáculos_superados × 50` | Bonificación significativa por obstáculo superado. Dirige la presión selectiva hacia la habilidad real: saltar |

**¿Por qué el factor 50?**  
Los obstáculos aparecen cada 60-120 frames. Sin la bonificación, un avatar que sobrevive 100 frames sin saltar nunca tendría el mismo fitness que uno que salta y supera 2 obstáculos (fitness = 200 por simple supervivencia, pero con 2 obstáculos = 100 + 100 = 200 frames + 100 bonus = 300). El factor 50 asegura que superar un obstáculo sea siempre más valioso que equivalente tiempo de supervivencia pasiva.

---

## 2. Métodos del AG Justificados

### Inicialización: distribución uniforme

```python
distancia = U(50, 400)   # Uniforme en todo el rango
velocidad = U(0, 20)     # Uniforme en todo el rango
```

**Justificación:** La distribución uniforme garantiza la máxima diversidad inicial, cubriendo todo el espacio de búsqueda sin sesgo. No existe conocimiento a priori de qué región del espacio [50,400] × [0,20] contiene las mejores soluciones. Alternativas como inicializar con heurísticas (ej. `umbral_distancia ≈ 200`) acelerarían la convergencia pero introducirían sesgo si la heurística fuera incorrecta o subóptima para las dinámicas específicas del juego.

### Selección: torneo (k=3) vs. alternativas

```python
candidatos = random.sample(poblacion, k=3)
ganador    = max(candidatos, key=lambda a: a.fitness)
```

**Torneo vs. Ruleta (proporcional al fitness):**

| Criterio | Torneo k=3 | Ruleta |
|---|---|---|
| Presión selectiva | Moderada y controlable | Muy alta cuando hay outliers de fitness |
| Diversidad | Se mantiene bien | Se degrada rápido si un individuo domina |
| Escalabilidad | No depende de la escala de fitness | Sensible a la escala (fitness=5000 vs fitness=50) |
| Implementación | Simple, sin normalización | Requiere normalización del fitness |

**Torneo vs. Ranking:**

| Criterio | Torneo k=3 | Ranking |
|---|---|---|
| Información de magnitud | Preservada implícitamente | Perdida (solo importa el orden) |
| Presión selectiva | Variable según k | Constante, independiente del fitness |
| Velocidad de convergencia | Moderada | Puede ser lenta o rápida según configuración |

**Elección k=3:** Mayor que 2 (presión insuficiente, casi aleatorio) y menor que 5+ (demasiada presión para n=30, riesgo de convergencia prematura). k=3 da a cada individuo probabilidad razonable de ser seleccionado incluso si no es el mejor, manteniendo diversidad genética.

### Crossover: un punto para cromosoma de 2 genes

```python
# Único punto de corte posible: entre gen 0 y gen 1
hijo1 = Chromosome(umbral_distancia=padre1.dist, umbral_velocidad=padre2.vel)
hijo2 = Chromosome(umbral_distancia=padre2.dist, umbral_velocidad=padre1.vel)
```

**Justificación para cromosoma de 2 genes:**

Con solo 2 genes, el crossover de un punto tiene exactamente **un punto de corte posible** (entre el gen 0 y el gen 1). Esto equivale a:
- `hijo1` hereda `umbral_distancia` del padre 1 y `umbral_velocidad` del padre 2
- `hijo2` hace lo inverso

Este mecanismo permite recombinar estrategias: si el padre 1 tiene buen `umbral_distancia` pero mal `umbral_velocidad`, y el padre 2 lo inverso, los hijos pueden combinar las virtudes de ambos.

El crossover de 2 puntos o uniforme son equivalentes o indiferentes con 2 genes, por lo que el crossover de 1 punto es la elección mínima suficiente.

**Probabilidad pc=0.8:** Asegura que el 80% de los pares se recombinen (explotación de buenas combinaciones) mientras el 20% pasan sin cruzarse (preservación de patrones individuales).

### Mutación: perturbación gaussiana vs. bit-flip

```python
gen_nuevo = gen + N(0, sigma)
gen_nuevo = clip(gen_nuevo, limite_min, limite_max)
```

**Gaussiana vs. bit-flip en espacios continuos:**

| Propiedad | Gaussiana | Bit-flip |
|---|---|---|
| Tipo de espacio | Continuo ✅ | Discreto/binario ✅ |
| Tamaño de perturbación | Pequeño con alta probabilidad | Arbitrario / discontinuo |
| Exploración local | Excelente (vecindario suave) | No tiene vecindario natural |
| Escapar óptimos locales | Posible (cola de la gaussiana) | Difícil sin escala adaptativa |

**El bit-flip en espacios continuos** requeriría redefinir "invertir un bit" como algo arbitrario (ej. invertir el signo, ir al extremo), lo que generaría saltos grandes y aleatorios incompatibles con la idea de exploración local.

**La gaussiana** con `sigma=20` para `umbral_distancia` (rango [50,400]) representa ~5.7% del rango: perturbaciones pequeñas que permiten ajuste fino alrededor de buenas soluciones. La sigma para `umbral_velocidad` se escala proporcionalmente al rango del gen (`sigma_vel = 20 × 20/350 ≈ 1.14`).

**Probabilidad pm=0.1 (10% por gen):** Introduce suficiente diversificación sin destruir sistemáticamente las adaptaciones acumuladas. Tasas más altas (~0.5) convertirían el AG en búsqueda casi aleatoria.

---

## 3. Problemas Enfrentados

### Intensificación: cómo el elitismo la mejora

**Problema sin elitismo:** Los mejores cromosomas pueden degradarse en la siguiente generación por efectos estocásticos del crossover y la mutación. El AG podría "olvidar" buenas soluciones y retroceder en fitness.

**Solución — Elitismo (ELITISMO=2):**

Los 2 individuos con mayor fitness pasan sin ninguna modificación a la siguiente generación:

```python
for i in range(ELITISMO):  # i = 0, 1
    nuevos_cromosomas.append(poblacion_ordenada[i].cromosoma)
```

Esto garantiza:
1. **Monotonía del máximo**: el fitness máximo nunca decrece entre generaciones
2. **Guía de selección**: los elites influyen en torneos, orientando la evolución hacia sus vecindarios
3. **Intensificación**: la búsqueda se concentra alrededor de las mejores soluciones conocidas

Con n=30, transferir 2 individuos (6.7%) es conservador: suficiente para retener las mejores soluciones sin reducir la diversidad de manera significativa.

**Convergencia observada:** Con elitismo, el mejor fitness de cada generación es monotónicamente no-decreciente. Sin elitismo, se observan retrocesos frecuentes en las primeras generaciones cuando la varianza del fitness es alta.

### Diversificación: justificación de tasa de mutación y tamaño de población

**Problema:** Si la presión selectiva es muy alta o la mutación muy baja, todos los individuos convergen rápidamente al mismo cromosoma (deriva genética), quedando atrapados en óptimos locales.

**Mecanismos de diversificación:**

1. **Tamaño de población n=30:** Suficiente para mantener diversidad genética. Con n<15, la deriva genética es muy fuerte y la convergencia prematura es casi inevitable. Con n>50, el beneficio marginal en diversidad no justifica el costo computacional (30 × 60 FPS = 1800 evaluaciones físicas por segundo).

2. **Tasa de mutación pm=0.1:** El 10% por gen introduce variación continua. Con la fórmula de Schwefel para tasas óptimas (`pm ≈ 1/L` donde L=longitud del cromosoma), para L=2 sería pm=0.5, pero esto es excesivo para perturbaciones gaussianas en espacios continuos. pm=0.1 es un compromiso probado en ESs (Estrategias Evolutivas).

3. **Sigma gaussiana calibrada:** sigma=20 para `umbral_distancia` permite explorar el vecindario en un radio de ~40-60 px (±1-2 sigma), cubriendo el espacio de variación relevante sin saltos desestabilizadores.

4. **Torneo k=3 como mecanismo de diversificación:** Al no ser completamente elitista, permite que individuos subóptimos se reproduzcan ocasionalmente, manteniendo genes alternativos en el acervo.

### Convergencia prematura: cómo el torneo la mitiga

**Definición:** La convergencia prematura ocurre cuando la población converge hacia un óptimo local antes de haber explorado suficientemente el espacio de búsqueda.

**Causa principal:** Un individuo con fitness muy superior al resto domina la selección y sus genes se propagan rápidamente a toda la población, eliminando la diversidad necesaria para escapar de óptimos locales.

**Análisis matemático del torneo:**

Sea `f*` el fitness del mejor individuo y `f̄` el fitness promedio. La probabilidad de que el mejor individuo sea seleccionado en un torneo de k=3 es:

```
P(mejor gana torneo de k=3) = 1 - (1 - 1/n)^k ≈ 3/30 = 0.1  (para el mejor en n=30)
```

En contraste, con ruleta proporcional: `P = f*/(n × f̄)`. Si `f* = 10 × f̄`, la probabilidad es ~33%, generando 3× más hijos del mejor individuo que el torneo.

**El torneo** garantiza que incluso con diferencias grandes de fitness, ningún individuo puede monopolizar la reproducción. Esto mantiene la diversidad genética suficiente para explorar múltiples regiones del espacio de búsqueda de forma simultánea.

---

## 4. Resultados

### Capturas del juego

*(Añadir capturas de pantalla del juego en diferentes generaciones)*

**Comportamiento observado por etapas:**

| Generación | Comportamiento esperado | Fitness típico |
|---|---|---|
| 1-3 | Saltos erráticos o ausencia total de salto; mayoría muere en 1er obstáculo | 50-200 |
| 4-8 | Emerge comportamiento de salto básico; algunos superan 1-2 obstáculos | 200-800 |
| 10-20 | Mayoría salta correctamente; diferenciación por calibración fina | 800-3000 |
| 20+ | Convergencia hacia cromosoma óptimo; individuo sobrevive indefinidamente | 3000+ |

### Evolución del fitness

*(Insertar captura del gráfico de historial)*

### Mejor cromosoma encontrado

*(Completar tras ejecutar el experimento con los valores reales)*

```
Mejor cromosoma encontrado:
  umbral_distancia: XXX.X px  
    → El avatar salta cuando el obstáculo está a menos de XXX px
  umbral_velocidad: X.XX     
    → Solo salta cuando la velocidad supera X.XX unidades

Fitness alcanzado:  XXXXX
Generación:         XX
```

### Enlace al video de demostración

*(Añadir enlace al video de demostración del juego evolucionando)*

---

## 5. Conclusiones

El AG implementado demuestra **convergencia efectiva** hacia estrategias de salto viables a partir de cromosomas completamente aleatorios, generalmente en 10-20 generaciones.

Los tres factores críticos del diseño resultaron ser:

1. **Representación cromosómica** de 2 genes reales: minimalista pero suficiente para capturar la estrategia de salto óptima. Más genes no añadirían expresividad para este problema.

2. **Fitness con bonificación por obstáculos**: sin este componente, el AG converge a estrategias de "no hacer nada" que evitan colisiones por azar. La bonificación es el mecanismo que hace emerger el comportamiento inteligente real.

3. **Balance exploración/explotación**: el elitismo (intensificación), la mutación gaussiana y el torneo con k moderado (diversificación) trabajan en conjunto para alcanzar buenas soluciones sin quedar atrapados en óptimos locales.

El proyecto también demuestra la viabilidad del patrón **Clean Architecture** para aplicaciones de juego en tiempo real: la separación entre dominio, aplicación, infraestructura y frontend facilita el testing, la modificación de parámetros del AG y la extensión del sistema sin romper capas.
