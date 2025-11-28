---
title: Solucionador de Puzzle (IA)
emoji: 🧩
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# 🧩 Solucionador de Rompecabezas Deslizante (N-Puzzle) con IA

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Stack](https://img.shields.io/badge/FullStack-Flask%20%7C%20Alpine.js%20%7C%20Tailwind-06b6d4)
![Deploy](https://img.shields.io/badge/Deploy-Hugging%20Face-FFD21E)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **🚀 [VER DEMO INTERACTIVA EN VIVO](https://huggingface.co/spaces/opablon/puzzle-solver)**

Esta aplicación es una implementación **Full-Stack** de un solucionador inteligente para el clásico rompecabezas deslizante (N-Puzzle). 

A diferencia de las implementaciones tradicionales que solo generan scripts, este proyecto es una **Web App interactiva** que permite al usuario cargar sus propias imágenes, mezclar el tablero en tiempo real y visualizar cómo la Inteligencia Artificial (A* o BFS) resuelve el problema paso a paso mediante animaciones en el DOM.

## ✨ Características Principales

* **Arquitectura Reactiva:** El frontend no recarga la página. Utiliza **Alpine.js** para gestionar el estado y **JavaScript** puro para animaciones de alto rendimiento a 60fps.
* **Diseño Moderno:** Interfaz construida con **Tailwind CSS**, totalmente responsiva (móvil/escritorio) y con Modo Oscuro nativo.
* **Visualización Real:** No genera GIFs estáticos. El tablero se renderiza dinámicamente cortando la imagen subida en el navegador.
* **Configuración Flexible:** Permite ajustar la velocidad de animación, la cantidad de mezclas y la semilla aleatoria.
* **Carga de Imágenes:** Soporta subida de archivos locales y URLs externas con bypass de restricciones (User-Agent spoofing).
* **Modo Interactivo y Gamificación:**
    - Bloqueo de interacción manual hasta que el usuario pulse **Mezclar**.
    - Hint superpuesto previo a la mezcla indicando “Antes de jugar, hacé clic en Mezclar”.
    - Métricas del usuario: tiempo y cantidad de movimientos manuales.
    - Overlay de victoria con botón **Jugar de nuevo** que reinicia con una nueva mezcla.
    - Coherencia de estados al mezclar y resolver luego de movimientos manuales.

## 🛠️ Stack de Tecnología

El proyecto evolucionó de un Notebook de análisis a una Aplicación Web moderna:

### Frontend
* **HTML5 Semántico & CSS3**
* **Tailwind CSS:** Para el diseño visual, layout responsivo y componentes de UI.
* **Alpine.js:** Para el manejo de estado reactivo (loading, visualización de resultados) y transiciones.
* **JavaScript (ES6+):** Lógica central de animación del tablero, manipulación del DOM y modo interactivo con bloqueo de controles durante animaciones.

### Backend
* **Python 3:** Lenguaje principal.
* **Flask:** Servidor web y API REST que procesa las imágenes y ejecuta los algoritmos.
* **PIL (Pillow):** Procesamiento y recorte de imágenes en el servidor.
* **NumPy:** Manejo eficiente de matrices para los estados del puzzle.

### Infraestructura & IA
* **Docker:** Contenerización de la aplicación para despliegue reproducible.
* **Hugging Face Spaces:** Plataforma de despliegue continuo (CD).
* **Algoritmos de Búsqueda:** Implementaciones puras de **A*** (con heurística Manhattan) y **BFS**.

## 🤖 Algoritmos Implementados

### 1. 🧠 A* (A-Estrella) - *Recomendado*
Es un algoritmo de búsqueda informada. Utiliza una "brújula" matemática para decidir qué movimiento es el más prometedor.
* **Heurística:** Distancia Manhattan (suma de distancias de cada pieza a su posición correcta).
* **Ventaja:** Encuentra la solución óptima (mínimos pasos) extremadamente rápido.

### 2. 🧪 BFS (Búsqueda en Anchura)
Algoritmo de fuerza bruta que explora el puzzle "nivel por nivel".
* **Ventaja:** Garantiza la solución óptima.
* **Desventaja:** Crecimiento exponencial de memoria. Útil para propósitos académicos en puzzles pequeños.
* **Benchmark:** El backend ejecuta A* y BFS (comparativa) y la UI muestra estadísticas (tiempo y estados explorados).

## 🚀 Ejecución Local

Si deseas correr el proyecto en tu máquina:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/opablon/Sliding-puzzle.git](https://github.com/opablon/Sliding-puzzle.git)
    cd Sliding-puzzle
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar el servidor:**
    ```bash
    python app.py
    ```
4.  Abrir `http://127.0.0.1:5000` en tu navegador.

## 🧭 Flujo de Interacción y Consistencia

* **Cargar/Iniciar:** Se muestra el tablero en estado resuelto con la imagen cortada y un hint que indica que primero se debe pulsar **Mezclar**.
* **Mezclar:** Antes de animar la mezcla, el tablero se restablece al estado resuelto; luego se anima la secuencia de mezclas recibida del backend y se habilita la interacción manual.
* **Resolver:** Si hiciste movimientos manuales, la UI restablece el tablero al **estado mezclado original** (provisto por el backend, aplanado a un arreglo de 9 números) y después anima la solución (A* paso a paso).
* **Jugar de nuevo:** Desde el overlay de victoria, el botón **Jugar de nuevo** solicita un nuevo puzzle al backend, re-renderiza el tablero y anima automáticamente la nueva mezcla.
* **Bloqueo durante animaciones:** Mientras se ejecuta una animación, el tablero deshabilita clics y los botones de control se deshabilitan para evitar entradas simultáneas.
* **Spinner y resultados:** El spinner cubre el panel derecho durante las solicitudes; al concluir, el área de resultados se expande y muestra las métricas.

## 🎓 Contexto del Proyecto

Este trabajo fue desarrollado como proyecto final para la asignatura **Taller de Programación III** de la Tecnicatura Universitaria en Inteligencia Artificial (Universidad Nacional de Hurlingham).