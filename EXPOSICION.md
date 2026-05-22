# 🎤 Guión de Exposición — Dino Runner GA

Este documento es tu **guión y material de lectura** para la presentación del proyecto de Inteligencia Artificial. Está diseñado para que puedas leerlo de manera fluida o utilizarlo como una guía estructurada paso a paso durante tu defensa o exposición.

---

## 📌 Introducción y Bienvenida
*(Tiempo estimado: 1 minuto)*

**Lo que debes decir:**
> "Buenos días, profesor y compañeros. Hoy les presentaremos nuestro proyecto de Inteligencia Artificial titulado **'Dino Runner GA'**.
> 
> El objetivo de este trabajo es desarrollar un entorno interactivo en tiempo real donde un avatar aprenda de manera autónoma a saltar obstáculos dinámicos mediante un **Algoritmo Genético**.
> 
> En lugar de programar manualmente las reglas de cuándo debe saltar el avatar, o utilizar técnicas tradicionales de control, hemos diseñado un sistema evolutivo donde los avatares empiezan sin saber qué hacer y, generación tras generación, logran desarrollar un comportamiento altamente refinado de supervivencia.
> 
> A continuación, les explicaremos en detalle cómo formulamos el problema, los operadores genéticos implementados, el balance entre exploración y explotación, y finalmente mostraremos la arquitectura de software y el funcionamiento en vivo."

---

## 🎯 Bloque 1: Formulación del Problema, Representación y Fitness
*(Tiempo estimado: 3 minutos)*

### 1. Representación del Cromosoma (La Solución)
**Lo que debes decir:**
> "Para que un algoritmo genético funcione, lo primero que debemos definir es **cómo representamos una solución en el código**. En nuestro caso, la solución representa la estrategia de salto de un avatar.
> 
> Implementamos una representación continua y minimalista de **dos genes de valor real** dentro de un objeto inmutable denominado `Chromosome`:
> 
> 1. El primer gen es el **`umbral_distancia`**: que define a cuántos píxeles de distancia de un obstáculo el avatar considera iniciar un salto. Su rango está limitado entre 50 y 400 píxeles.
> 2. El segundo gen es el **`umbral_velocidad`**: que representa la velocidad mínima a la que debe desplazarse el juego para que el salto tenga sentido. Su rango va de 0 a 20 unidades.
> 
> **¿Dónde está en el código?**  
> Si observamos el archivo `backend/domain/value_objects/chromosome.py`, veremos la clase `Chromosome` estructurada como un `dataclass` inmutable. Los límites físicos de estos genes están parametrizados en `backend/config.py` bajo las constantes `UMBRAL_DISTANCIA_MIN` y `MAX`."

### 2. Regla de Decisión (Física del Juego)
**Lo que debes decir:**
> "Cada frame de la simulación física, cuando el avatar se encuentra en el suelo, consulta a su 'cerebro' o cromosoma y toma una decisión de salto basada en la siguiente regla lógica:
> *Si la distancia al obstáculo más cercano delante del avatar es menor que su `umbral_distancia` **Y** la velocidad actual de la pantalla es mayor que su `umbral_velocidad`, entonces se aplica una velocidad vertical de salto.*
> 
> **¿Dónde está en el código?**  
> Esta regla de decisión se ejecuta en tiempo real en la función `decidir_salto` del archivo `backend/domain/use_cases/run_simulation.py`."

### 3. La Función de Fitness (Medida de Éxito)
**Lo que debes decir:**
> "Para evaluar qué tan bueno es un avatar, formulamos una función de fitness con la siguiente estructura matemática:
> 
> $$\text{Fitness} = \text{frames\_sobrevividos} + (\text{obstaculos\_superados} \times 50)$$
> 
> **Justificación del diseño:**  
> Si solo midiéramos el tiempo de vida (los frames sobrevividos), el algoritmo genético podría converger a una solución perezosa: avatares que no hacen nada, se quedan parados y sobreviven el tiempo base hasta chocar con el primer obstáculo. 
> 
> Para generar una verdadera presión selectiva hacia el aprendizaje, añadimos una **bonificación muy significativa de 50 puntos por cada obstáculo superado**. Como los obstáculos aparecen cada 60 a 120 frames, una recompensa de 50 puntos asegura que superar un obstáculo siempre sea drásticamente más valioso que simplemente sobrevivir sin actuar.
> 
> **¿Dónde está en el código?**  
> El cálculo se efectúa en el método `calcular_fitness` de la entidad `Avatar` en `backend/domain/entities/avatar.py`, y es evaluado de forma masiva por el caso de uso `evaluar_poblacion` en `backend/domain/use_cases/evaluate_fitness.py` cuando los individuos mueren."

---

## 🧬 Bloque 2: Métodos del Algoritmo Genético Justificados
*(Tiempo estimado: 4 minutos)*

### 1. Inicialización de la Población
**Lo que debes decir:**
> "Al iniciar la simulación, no sabemos qué valores de distancia o velocidad son los mejores para esquivar los obstáculos. Por lo tanto, implementamos un método de **Inicialización Aleatoria con Distribución Uniforme**.
> 
> **Justificación:**  
> La distribución uniforme garantiza que cubramos equitativamente todo el espacio de búsqueda tridimensional sin ningún sesgo inicial. Si usáramos una distribución normal centrada en un valor heurístico inventado por nosotros, podríamos limitar al algoritmo de descubrir estrategias de salto no convencionales y eficientes.
> 
> **¿Dónde está en el código?**  
> Se encuentra en la función `inicializar_poblacion` del archivo `backend/domain/use_cases/evolve_population.py`, utilizando la función de NumPy `random.uniform` para rellenar la población inicial."

### 2. Método de Selección: Torneo ($k=3$)
**Lo que debes decir:**
> "Para seleccionar a los padres que se van a reproducir, elegimos **Selección por Torneo con $k=3$**.
> 
> **Justificación frente a alternativas:**  
> *   **Contra la Ruleta (proporcional al fitness):** Si un individuo de la población tiene un fitness extremadamente alto respecto a los demás (un 'outlier'), en el método de ruleta acaparará casi todo el círculo de selección, reproduciéndose masivamente y eliminando de inmediato la diversidad genética en una sola generación. El torneo de $k=3$ modera esto: el mejor individuo solo compite contra otros dos elegidos al azar, limitando su dominio reproductivo.
> *   **Contra el Ranking:** El torneo es sumamente eficiente y mantiene la escala de magnitud del fitness sin requerir transformaciones u ordenamientos costosos de la población completa en cada selección.
> *   **Elección de $k=3$:** Un torneo de $k=2$ ejerce muy poca presión selectiva (casi selección aleatoria), y un torneo de $k \ge 5$ ejerce demasiada presión en una población de 30 individuos, provocando convergencia prematura. $k=3$ es el punto de balance óptimo.
> 
> **¿Dónde está en el código?**  
> Está implementado en `seleccion_torneo` en `backend/domain/use_cases/evolve_population.py`."

### 3. Método de Crossover: Un Punto
**Lo que debes decir:**
> "Para combinar la información de los padres, aplicamos **Crossover de un punto con una probabilidad $p_c = 0.8$**.
> 
> **Justificación:**  
> Dado que nuestro cromosoma cuenta únicamente con **dos genes**, solo existe un punto de corte lógico (entre el gen de distancia y el gen de velocidad). El cruce consiste en intercambiar estos genes entre los dos padres para dar origen a dos nuevos hijos.
> Esto permite explotar combinaciones ganadoras: por ejemplo, si el Padre 1 tiene un excelente `umbral_distancia` pero un mal `umbral_velocidad`, y el Padre 2 tiene un excelente `umbral_velocidad` pero una mala distancia, sus hijos pueden heredar las mejores partes de ambos mundos y superar el desempeño de sus progenitores.
> 
> **¿Dónde está en el código?**  
> Ver la función `crossover_un_punto` en `backend/domain/use_cases/evolve_population.py`."

### 4. Método de Mutación: Perturbación Gaussiana
**Lo que debes decir:**
> "En lugar del clásico 'bit-flip' o inversión de bits que se utiliza en cromosomas binarios, para nuestro espacio continuo de números reales implementamos una **Mutación por Perturbación Gaussiana** con probabilidad $p_m = 0.1$ por gen.
> 
> **Justificación:**  
> Aplicar bit-flip en números flotantes reales causaría cambios erráticos y gigantescos incompatibles con una búsqueda local suave. La mutación gaussiana suma un ruido aleatorio basado en una campana de Gauss ($\mathcal{N}(0, \sigma)$). Esto significa que la gran mayoría de las mutaciones serán pequeñas perturbaciones (permitiendo un ajuste fino y milimétrico de la estrategia de salto), pero ocasionalmente se producirán perturbaciones grandes (permitiendo escapar de óptimos locales).
> Además, calibramos el factor $\sigma$ (desviación estándar) proporcionalmente a la escala de cada gen: $\sigma_{distancia} = 20.0$ (sobre un rango de 350 píxeles) y $\sigma_{velocidad} \approx 1.14$ (sobre un rango de 20 unidades).
> 
> **¿Dónde está en el código?**  
> Ver la función `mutacion_gaussiana` en `backend/domain/use_cases/evolve_population.py`."

---

## ⚖️ Bloque 3: Balance de Intensificación, Diversificación y Problemas Enfrentados
*(Tiempo estimado: 3 minutos)*

### 1. Intensificación y cómo el Elitismo la mejora
**Lo que debes decir:**
> "Uno de los principales problemas en algoritmos genéticos estocásticos es el riesgo de **perder las mejores soluciones** debido a mutaciones dañinas o cruces desfavorables.
> 
> Para solucionar esto y mejorar la **Intensificación** (explotar las mejores soluciones conocidas), implementamos **Elitismo con un factor de 2**.
> 
> **Fundamentación:**  
> En cada transición generacional, los 2 avatares con el fitness más alto pasan **completamente intactos** (sin crossover y sin mutación) a la siguiente población. Esto garantiza matemáticamente la monotonía del máximo, es decir, el mejor fitness registrado nunca retrocederá de una generación a otra y nos enfocaremos firmemente en explotar esa zona del espacio de búsqueda.
> 
> **¿Dónde está en el código?**  
> En la función `evolucionar` de `backend/domain/use_cases/evolve_population.py` (líneas 184-186), donde extraemos directamente del arreglo ordenado a los elites antes de reproducir al resto de la población."

### 2. Diversificación (Mantenimiento de la Variabilidad)
**Lo que debes decir:**
> "Por otro lado, la **Diversificación** es fundamental para explorar nuevas alternativas y no quedar atrapados en óptimos locales. Si todos los individuos convergen muy rápido al mismo cromosoma, el algoritmo se estanca.
> 
> Para mejorar la diversificación, tomamos tres decisiones clave:
> 1. Un **tamaño de población de 30 individuos** ($TAMANO\_POBLACION = 30$), que es óptimo para balancear la riqueza del acervo genético y el costo computacional de ejecutar físicas de colisión a 60 FPS en Python.
> 2. Una **probabilidad de mutación por gen de $0.1$ ($10\%$)**, que inyecta variabilidad constante y novedosa en cada generación.
> 3. El uso del torneo con $k=3$, que permite que cromosomas mediocres pero con diversidad genética sobrevivan ocasionalmente para aportar a la variabilidad de la población.
> 
> **¿Dónde está en el código?**  
> Todas estas constantes están unificadas en `backend/config.py` para asegurar que no existan 'números mágicos' ocultos en la lógica."

---

## 🏛️ Bloque 4: Arquitectura y Demostración Práctica
*(Tiempo estimado: 2 minutos)*

### 1. Clean Architecture en un Juego en Tiempo Real
**Lo que debes decir:**
> "Un aspecto muy fuerte de este proyecto es que no está desarrollado como un script monolítico desordenado. Hemos aplicado el patrón **Clean Architecture** (Arquitectura Limpia), aislando las capas de la aplicación:
> 
> *   **Capa de Dominio:** Contiene las reglas del juego y la evolución puras. No sabe nada de páginas web ni de bases de datos. Aquí están las entidades (`Avatar`, `Obstacle`) y los casos de uso (`tick_simulacion`, `evolucionar`, `evaluar_fitness`).
> *   **Capa de Aplicación:** Coordina el flujo continuo de simulación a través de la clase `GAController` y el `game_loop`.
> *   **Capa de Infraestructura y UI:** Implementa el servidor WebSocket utilizando **FastAPI** y **Uvicorn** en `backend/infrastructure/websocket_server.py`, el cual envía los datos de la física a 60 FPS hacia una interfaz web desarrollada en HTML5 Canvas."

### 2. Conclusión y Demo en Vivo
**Lo que debes decir:**
> "Para concluir, el algoritmo demuestra una **convergencia asombrosa**. En las generaciones 1 a 3, los avatares tienen comportamientos caóticos o simplemente no saltan. Hacia la generación 5, aprenden a superar el primer obstáculo. Para la generación 10 a 15, la población converge hacia una nube compacta de soluciones óptimas en el gráfico de dispersión, logrando avatares que corren de forma indefinida superando obstáculos veloces.
> 
> Ahora, profesor, pasaremos a mostrarle la simulación interactiva y el dashboard de analíticas en tiempo real..."
> 
> *(Aquí abres el navegador web en `http://localhost:8000`, muestras a los dinosaurios saltando y señalas los gráficos de Chart.js del HUD, especialmente el Scatter Plot que muestra cómo los cromosomas de los avatares activos se van agrupando en una zona específica a medida que pasan las generaciones).*

---

## 💡 Consejos de Oro para Responder Preguntas del Jurado

Si el jurado o el profesor te pregunta...

1. **¿Por qué usaron Python y FastAPI en lugar de solo JavaScript en el frontend?**
   *   *Respuesta:* "Queríamos desacoplar por completo el motor de simulación física y el algoritmo genético de la interfaz visual. Al implementarlo en Python bajo Clean Architecture, el núcleo de nuestro algoritmo de IA queda completamente limpio y protegido, facilitando las pruebas unitarias y su escalabilidad a otros frameworks visuales (por ejemplo, podríamos cambiar el frontend HTML5 por Pygame o Unity y el motor genético no requeriría una sola línea de modificación)."
2. **¿Qué pasa si incrementan la velocidad de simulación en el frontend?**
   *   *Respuesta:* "Implementamos un parámetro de aceleración en el backend. Cuando el usuario selecciona velocidad de $2\times, 5\times$ o $10\times$, el bucle en `backend/application/game_loop.py` ejecuta múltiples ticks físicos por cada tick visual enviado. Esto permite que la evolución progrese de forma extremadamente rápida en segundos sin perder precisión en la física de colisiones."
3. **¿Cómo garantizan que la mutación gaussiana no dé valores absurdos o negativos?**
   *   *Respuesta:* "Utilizamos la función `np.clip` inmediatamente después de sumar el ruido gaussiano en la función `mutacion_gaussiana`. Esto asegura que los genes mutados permanezcan estrictamente encajonados en los rangos biológicos y físicos definidos en `config.py` (por ejemplo, que la distancia al obstáculo nunca sea menor a 50 ni mayor a 400 píxeles)."
