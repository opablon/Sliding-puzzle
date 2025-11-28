# 🧩 Especificaciones Técnicas: Solucionador de N-Puzzle con IA

## 1. Resumen del Proyecto
Aplicación web Full-Stack que resuelve rompecabezas deslizantes (Sliding Puzzles) utilizando algoritmos de Inteligencia Artificial (A* y BFS). La aplicación permite cargar imágenes propias, visualizar el proceso de mezcla y animar la solución paso a paso en el navegador.

## 2. Stack Tecnológico
* **Backend:** Python 3.10+, Flask (Servidor), Gunicorn (Producción).
* **Procesamiento de Imágenes:** PIL (Pillow), NumPy.
* **Frontend:** * **HTML5** (Single Page Application).
    * **Tailwind CSS** (vía CDN) para estilos y responsividad.
    * **Alpine.js** (vía CDN) para manejo de estado, reactividad y transiciones.
* **Despliegue:** Docker en Hugging Face Spaces.
* **Control de Versiones:** Git + Git LFS.

## 3. Arquitectura del Sistema

### Backend (`app.py`)
* **Rol:** "Cerebro Lógico". No genera vistas ni animaciones.
* **Endpoint Principal:** `POST /solve`.
    * Recibe: Imagen (archivo o URL), Configuración (Algoritmo, Semilla, Mezclas).
    * Procesa: Redimensiona y recorta la imagen a 3x3.
    * Lógica: Ejecuta la mezcla y el algoritmo de búsqueda (A* o BFS).
    * Retorna JSON:
        * `estado_inicial_numerico`: Matriz 3x3.
        * `imagen_skin_base64`: String Base64 de la imagen procesada.
        * `movimientos_solucion`: Lista de strings ['ARRIBA', 'DERECHA'...].
        * `stats_data`: Diccionario con métricas (tiempo, nodos explorados).
    * Fallback de imagen: Si el usuario no sube archivo ni proporciona URL, se usa automáticamente `static/assets/default.jpg` para permitir iniciar sin selección previa.

### Frontend (`templates/index.html`)
* **Rol:** Interfaz interactiva de estados (SPA).
* **Arquitectura:** Alpine.js gestiona una máquina de estados finitos.
* **Alpine.js State (`x-data`):**
    * `initialState`: Tablero mezclado (recibido del backend).
    * `currentPuzzleState`: Estado visual actual del tablero (puede ser resuelto, mezclado o intermedio).
    * `solutionMoves`: Lista de movimientos para resolver.
    * `mixMoves`: Lista de movimientos que se usaron para mezclar.
    * `isAnimating`: Booleano para bloquear controles durante animaciones. Mientras `isAnimating` es true, se deshabilitan los botones de control (Mezclar/Resolver/Limpiar) y se deshabilitan los clics en el tablero (`pointer-events: none`).
    * Métricas de Usuario (gamificación):
        * `userMovesCount`: Cantidad de movimientos manuales realizados desde la mezcla.
        * `userStartTime`: Timestamp (ms) del primer movimiento manual.
        * `userWon`: Bandera booleana indicando si el usuario resolvió manualmente.
        * `userTimeElapsed`: Tiempo en segundos desde `userStartTime` hasta victoria.
* **Lógica de Animación:**
    * `animatePuzzle(moves)`: Función asíncrona que ejecuta cambios visuales secuenciales en el tablero.
 * **Lógica de Interacción Manual:**
     * `intentarMover(r,c)`: Valida adyacencia al vacío, ejecuta intercambio y actualiza métricas. Detecta victoria comparando el estado con `[1,2,3,4,5,6,7,8,0]`.
     * Overlay de Victoria: `#win-overlay` se muestra al ganar, bloquea interacción y expone tiempo y movimientos.

## 4. Reglas de Negocio y Limitaciones
1.  **Tamaño del Puzzle:** Forzado a **3x3** en el backend para evitar timeouts de servidor en entornos gratuitos (Hugging Face Spaces).
2.  **Algoritmos:**
    * **A* (A-Star):** Heurística de Distancia Manhattan. Prioridad por velocidad.
    * **BFS:** Para demostración académica (garantiza optimidad pero explora más nodos).
3.  **Manejo de Errores:** El backend captura excepciones y retorna códigos 500 con mensajes JSON. El frontend los muestra al usuario.

## 5. Guía de Estilo (UI/UX)
* **Tema:** Modo Oscuro ("Dark Mode").
* **Flujo de Usuario (Interactivo):**
    1.  **Inicio:** Usuario carga imagen y configuración.
    2.  **Carga:** Al dar "Cargar/Iniciar", el backend calcula todo, pero la UI muestra el **Puzzle Resuelto** (imagen completa).
    3.  **Interacción 1 (Mezclar):** Usuario hace clic en "Mezclar". La app anima las piezas desordenándose rápidamente hasta llegar al estado mezclado.
    4.  **Interacción 2 (Resolver):** Usuario hace clic en "Resolver". Antes de resolver, la UI restablece el tablero al **estado mezclado original** recibido del backend (aplanado si viene 3x3), deshaciendo movimientos manuales del usuario; luego anima las piezas ordenándose (A*).
    5.  **Consistencia de estados:** Al iniciar "Mezclar" se restablece el tablero al **estado resuelto** inmediatamente para animar la mezcla desde un estado conocido.
    6.  **Victoria Manual:** Si el usuario resuelve manualmente (clicks), se muestra overlay con tiempo y movimientos y se deshabilita el tablero hasta un nuevo "Mezclar".
* **Visualización:** El tablero es el protagonista central. Los controles aparecen/desaparecen según el estado.