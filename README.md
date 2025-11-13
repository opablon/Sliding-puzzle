# 🧩 Solucionador de Rompecabezas Deslizante (N-Puzzle) con IA

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Algoritmos](https://img.shields.io/badge/Algoritmos-BFS%20%7C%20A*-%23f0db4f)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Este proyecto es un solucionador inteligente para el clásico rompecabezas deslizante (N-Puzzle). A partir de cualquier imagen, el programa la divide en una cuadrícula (ej. 4x4), la mezcla de forma garantizada para que tenga solución, y luego utiliza algoritmos de búsqueda de Inteligencia Artificial para encontrar el camino más corto de vuelta al estado original.

El resultado final es una animación GIF que muestra el puzzle resolviéndose paso a paso.

## Demo de la Solución

![Demo de Solución](assets/solucion.gif)

## 🤖 Algoritmos Implementados

Una parte clave del proyecto es la implementación y comparación de dos algoritmos de búsqueda fundamentales:

### 1. BFS (Búsqueda en Anchura)
Es un algoritmo de "fuerza bruta" que explora el puzzle "nivel por nivel".
* **Ventaja:** Garantiza encontrar la solución óptima (el menor número de movimientos).
* **Desventaja:** Es computacionalmente inviable para puzzles de más de 3x3, ya que la cantidad de estados a explorar crece exponencialmente.

### 2. 🧠 A* (A-Estrella)
Es un algoritmo de "búsqueda inteligente" o "informada". Prioriza qué caminos explorar basándose en la fórmula `f = g + h`:
* **`g(n)` (Costo Real):** El número de movimientos ya realizados para llegar al estado actual.
* **`h(n)` (Heurística):** Una estimación de lo que falta para llegar al objetivo.
* **Heurística Utilizada:** **Distancia Manhattan**, que suma la distancia (en filas y columnas) que cada pieza debe moverse para llegar a su posición correcta.

A* encuentra la misma solución óptima que BFS, pero de forma muchísimo más eficiente, permitiendo resolver puzzles de 4x4 en un tiempo razonable.

## ✨ Características Principales

* **Carga de Imágenes Personalizada:** Utiliza cualquier imagen desde una URL o un archivo local.
* **Visualización Gráfica:** Usa la librería PIL (Pillow) para crear y animar el tablero con la imagen real, no solo con números.
* **Garantía de Solución:** El puzzle se mezcla realizando un 'camino aleatorio inverso' desde el estado objetivo, asegurando que siempre sea resoluble.
* **Exportación a GIF:** Guarda la animación de la solución completa como un archivo `solucion.gif`.

## 🛠️ Stack de Tecnología

* Python 3
* Google Colab / Jupyter Notebook
* **PIL (Pillow):** Para el recorte, manipulación y ensamblado de imágenes.
* **NumPy:** Para la conversión de imágenes para su visualización.
* **Matplotlib:** Para mostrar la imagen original y los estados inicial/final.
* **`heapq`:** Para la implementación de la cola de prioridad de A*.
* **`deque`:** Para la implementación de la cola de BFS.

## 🚀 Uso (en Google Colab)

1.  Abrir el archivo `.ipynb` en Google Colab.
2.  Ejecutar la celda de `imports`.
3.  Configurar los parámetros en la celda de configuración (puedes cambiar `URL_IMAGEN`, `TAMANO_PUZZLE`, `ALGORITMO`, `MOVIMIENTOS`, etc.).
4.  Ejecutar todas las celdas.
5.  El programa mostrará la solución animada y guardará un `solucion.gif` en el entorno de Colab.

## 🎓 Contexto del Proyecto

Este trabajo fue desarrollado como proyecto final para la asignatura **Taller de Programación III** de la Tecnicatura Universitaria en Inteligencia Artificial (Universidad Nacional de Hurlingham).
