import numpy as np
from collections import deque
import random
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import io
import base64
import heapq
import time
import os

from flask import Flask, render_template, request, jsonify

ESPACIO_VACIO = 0 # Constante para representar el espacio vacío

def cargar_imagen(url_o_ruta, tamano, REDIMENSION_IMAGEN):
    """
    Carga una imagen desde:
      - URL (string que empiece por http)
      - ruta local (string)
      - objeto file-like (por ejemplo `request.files['imagen']`)

    La recorta a un cuadrado, la redimensiona y la divide en n*n piezas.
    """
    # URL remota
    if isinstance(url_o_ruta, str) and url_o_ruta.startswith('http'):
        # Algunos servidores bloquean peticiones sin User-Agent (p.ej. Wikimedia).
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        respuesta = requests.get(url_o_ruta, headers=headers)
        # Lanzar excepción si la descarga no fue exitosa (4xx/5xx)
        respuesta.raise_for_status()
        imagen = Image.open(BytesIO(respuesta.content))

    # Ruta local
    elif isinstance(url_o_ruta, str):
        imagen = Image.open(url_o_ruta)

    # File-like (por ejemplo request.files['imagen'])
    elif hasattr(url_o_ruta, 'read'):
        # Leemos el contenido en memoria y lo abrimos con PIL
        contenido = url_o_ruta.read()
        imagen = Image.open(BytesIO(contenido))

    else:
        raise ValueError("Tipo de entrada de imagen no soportado")

    lado_minimo = min(imagen.size)
    imagen = imagen.crop((0, 0, lado_minimo, lado_minimo))
    imagen = imagen.resize(REDIMENSION_IMAGEN)

    piezas = []
    ancho_pieza = imagen.width // tamano
    alto_pieza = imagen.height // tamano

    for i in range(tamano):
        for j in range(tamano):
            izquierda = j * ancho_pieza
            superior = i * alto_pieza
            derecha = izquierda + ancho_pieza
            inferior = superior + alto_pieza

            pieza = imagen.crop((izquierda, superior, derecha, inferior))
            piezas.append(pieza)

    tupla_tamano_pieza = (ancho_pieza, alto_pieza)

    return imagen, piezas, tupla_tamano_pieza

def crear_mapas_y_estados(tamano, lista_piezas, tamano_pieza):
    """
    Crea los mapeos de número->imagen y número->posición_objetivo.
    """
    mapa_piezas = {}
    mapa_objetivo = {}
    objetivo_numerico = []

    num_pieza = 1
    for f in range(tamano):
        fila = []
        for c in range(tamano):
            if f == tamano - 1 and c == tamano - 1:
                # Caso especial: la última pieza (abajo a la derecha) es el espacio vacío
                fila.append(ESPACIO_VACIO)
                mapa_piezas[ESPACIO_VACIO] = Image.new('RGB', tamano_pieza, color='black')
                mapa_objetivo[ESPACIO_VACIO] = (f, c)
            else:
                # Caso normal: todas las demás piezas
                fila.append(num_pieza)
                mapa_piezas[num_pieza] = lista_piezas[num_pieza - 1]
                mapa_objetivo[num_pieza] = (f, c)
                num_pieza += 1
        objetivo_numerico.append(fila)

    estado_objetivo_tupla = tuple(tuple(fila) for fila in objetivo_numerico)
    return mapa_piezas, mapa_objetivo, estado_objetivo_tupla

def mezclar_puzzle(estado_objetivo, num_movimientos, semilla_aleatoria):
    """
    Mezcla el puzzle realizando una caminata aleatoria desde el estado objetivo.
    Evita movimientos que deshacen el movimiento anterior.
    """
    random.seed(semilla_aleatoria)

    estado_actual = estado_objetivo
    ultimo_movimiento = None
    opuestos = {'ARRIBA': 'ABAJO', 'ABAJO': 'ARRIBA', 'IZQUIERDA': 'DERECHA', 'DERECHA': 'IZQUIERDA'}
    movimientos_realizados = []

    for _ in range(num_movimientos):
        sucesores = generar_sucesores(estado_actual)

        # Filtra el movimiento opuesto al último realizado
        if ultimo_movimiento:
            movimiento_opuesto = opuestos[ultimo_movimiento]
            sucesores_filtrados = [s for s in sucesores if s[1] != movimiento_opuesto]

            # Solo usa la lista filtrada si no nos deja sin opciones
            if sucesores_filtrados:
                sucesores = sucesores_filtrados

        # Elige un movimiento al azar
        nuevo_estado, ultimo_movimiento = random.choice(sucesores)
        estado_actual = nuevo_estado
        movimientos_realizados.append(ultimo_movimiento)

    return estado_actual, movimientos_realizados

def encontrar_vacio(estado):
    """
    Encuentra la posición (fila, columna) del espacio vacío (ESPACIO_VACIO).
    """
    tamano = len(estado)
    for f in range(tamano):
        for c in range(tamano):
            if estado[f][c] == ESPACIO_VACIO:
                return f, c
    return -1, -1

def generar_sucesores(estado):
    """
    Genera todos los estados sucesores válidos (numéricos).
    """
    tamano = len(estado)
    f_vacio, c_vacio = encontrar_vacio(estado)
    sucesores = []
    movimientos = [
        (-1, 0, 'ARRIBA'), (1, 0, 'ABAJO'),
        (0, -1, 'IZQUIERDA'), (0, 1, 'DERECHA')
    ]

    for df, dc, nombre in movimientos:
        nueva_f, nueva_c = f_vacio + df, c_vacio + dc

        if 0 <= nueva_f < tamano and 0 <= nueva_c < tamano:
            lista_estado = [list(fila) for fila in estado]

            # Intercambio
            lista_estado[f_vacio][c_vacio] = lista_estado[nueva_f][nueva_c]
            lista_estado[nueva_f][nueva_c] = ESPACIO_VACIO

            nuevo_estado = tuple(tuple(fila) for fila in lista_estado)
            sucesores.append((nuevo_estado, nombre))
    return sucesores

def construir_estado_imagen(estado, mapa_piezas, tamano_pieza):
    """
    Construye una imagen PIL a partir de un estado NUMÉRICO.
    """
    tamano = len(estado)
    ancho_pieza, alto_pieza = tamano_pieza
    ancho_total = ancho_pieza * tamano
    alto_total = alto_pieza * tamano

    lienzo = Image.new('RGB', (ancho_total, alto_total))
    dibujo = ImageDraw.Draw(lienzo)

    for idx_f, fila in enumerate(estado):
        for idx_c, num_pieza in enumerate(fila):
            pos_x = idx_c * ancho_pieza
            pos_y = idx_f * alto_pieza

            img_pieza = mapa_piezas[num_pieza]

            lienzo.paste(img_pieza, (pos_x, pos_y))

            # Dibuja el borde
            dibujo.rectangle(
                [pos_x, pos_y, pos_x + ancho_pieza - 1, pos_y + alto_pieza - 1],
                outline='black',
                width=1
            )
    return lienzo

def aplicar_movimiento(estado, movimiento):
    """
    Aplica un movimiento a un estado numérico, reutilizando la lógica
    de 'generar_sucesores' para evitar duplicar código.
    """
    # Genera todos los movimientos válidos desde el estado actual
    for nuevo_estado, nombre_movimiento in generar_sucesores(estado):

        # Si el movimiento generado coincide con el que queremos aplicar...
        if nombre_movimiento == movimiento:

            # ...devuelve ese nuevo estado.
            return nuevo_estado

    # Si el movimiento no se encontró (no era válido), devuelve el estado original
    return estado

def resolver_puzzle_bfs(estado_inicial, estado_objetivo):
    """
    Resuelve el puzzle usando BFS. Devuelve (movimientos_solucion, stats_dict).
    """
    start_time = time.time()
    if estado_inicial == estado_objetivo:
        return [], {'estados': 0, 'tiempo': time.time() - start_time}

    cola = deque([(estado_inicial, [])])
    visitados = {estado_inicial}

    while cola:
        estado_actual, ruta_actual = cola.popleft()
        for nuevo_estado, movimiento in generar_sucesores(estado_actual):
            if nuevo_estado not in visitados:
                visitados.add(nuevo_estado)
                nueva_ruta = ruta_actual + [movimiento]
                if nuevo_estado == estado_objetivo:
                    return nueva_ruta, {'estados': len(visitados), 'tiempo': time.time() - start_time}
                cola.append((nuevo_estado, nueva_ruta))
    # No se encontró solución dentro del espacio explorado
    return None, {'estados': len(visitados), 'tiempo': time.time() - start_time}

def heuristica_manhattan(estado_actual, posiciones_objetivo):
    """
    Calcula la distancia Manhattan usando números y el mapa pre-calculado.
    """
    tamano = len(estado_actual)
    distancia_total = 0
    for f_actual in range(tamano):
        for c_actual in range(tamano):
            num_pieza = estado_actual[f_actual][c_actual]
            if num_pieza != ESPACIO_VACIO: # Ignora el ESPACIO_VACIO
                f_obj, c_obj = posiciones_objetivo[num_pieza]
                distancia_total += abs(f_actual - f_obj) + abs(c_actual - c_obj)
    return distancia_total

def resolver_puzzle_a_estrella(estado_inicial, estado_objetivo, mapa_objetivo):
    """
    Resuelve el puzzle usando A* y la heurística de Manhattan.
    Devuelve (movimientos_solucion, stats_dict).
    """
    start_time = time.time()
    if estado_inicial == estado_objetivo:
        return [], {'estados': 0, 'tiempo': time.time() - start_time}

    costo_g_inicial = 0
    costo_total_inicial = costo_g_inicial + heuristica_manhattan(estado_inicial, mapa_objetivo)

    contador = 0
    frontera = [
        (costo_total_inicial, contador, costo_g_inicial, estado_inicial, [])
    ]
    costo_g_registrado = {estado_inicial: costo_g_inicial}

    while frontera:
        _, _, costo_g_actual, estado_actual, ruta_actual = heapq.heappop(frontera)

        if estado_actual == estado_objetivo:
            return ruta_actual, {'estados': len(costo_g_registrado), 'tiempo': time.time() - start_time}

        if costo_g_actual > costo_g_registrado.get(estado_actual, float('inf')):
            continue

        for nuevo_estado, movimiento in generar_sucesores(estado_actual):
            nuevo_costo_g = costo_g_actual + 1
            if nuevo_costo_g < costo_g_registrado.get(nuevo_estado, float('inf')):
                costo_g_registrado[nuevo_estado] = nuevo_costo_g
                nuevo_costo_total = nuevo_costo_g + heuristica_manhattan(nuevo_estado, mapa_objetivo)
                contador += 1
                heapq.heappush(frontera, (nuevo_costo_total, contador, nuevo_costo_g, nuevo_estado, ruta_actual + [movimiento]))

                # no more in-loop stats appending
    # No se encontró solución
    return None, {'estados': len(costo_g_registrado), 'tiempo': time.time() - start_time}

# --- RUTAS FLASK ---

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    """
    Endpoint para resolver el puzzle. Lee el formulario y archivo enviado,
    fuerza tamaño 3x3 (TAMANO_PUZZLE=3), mezcla según semilla/mezclas,
    resuelve con A* y BFS.
    """
    # Forzamos 3x3 para la demo rápida
    TAMANO_PUZZLE = 3
    REDIMENSION_IMAGEN = (300, 300)

    try:
        # 1. Parámetros
        semilla = request.form.get('semilla', '')
        try:
            semilla_int = int(semilla) if semilla != '' else None
        except ValueError:
            semilla_int = None

        try:
            num_mezclas = int(request.form.get('cantidad_mezclas', 30))
        except (ValueError, TypeError):
            num_mezclas = 30

        # 2. Imagen
        uploaded_file = request.files.get('imagen')
        image_url = (request.form.get('image-url') or '').strip()
        
        imagen_fuente = None
        if uploaded_file and getattr(uploaded_file, 'filename', ''):
            imagen_fuente = uploaded_file
        elif image_url:
            imagen_fuente = image_url
        else:
            # Imagen por defecto si no se carga archivo ni URL
            default_path = os.path.join('static', 'assets', 'default.jpg')
            imagen_fuente = default_path

        imagen_completa, lista_piezas, tamano_pieza = cargar_imagen(imagen_fuente, TAMANO_PUZZLE, REDIMENSION_IMAGEN)
        
        # 3. Preparar
        mapa_piezas, mapa_objetivo, estado_objetivo = crear_mapas_y_estados(TAMANO_PUZZLE, lista_piezas, tamano_pieza)
        
        # 4. Mezclar
        estado_inicial, movimientos_mezcla = mezclar_puzzle(estado_objetivo, num_mezclas, semilla_int)

        # 5. BENCHMARK: Ejecutar AMBOS
        # A*
        solucion_astar, stats_astar = resolver_puzzle_a_estrella(estado_inicial, estado_objetivo, mapa_objetivo)
        # BFS
        solucion_bfs, stats_bfs = resolver_puzzle_bfs(estado_inicial, estado_objetivo)

        # Usamos la solución A* para la animación visual
        movimientos_solucion = solucion_astar if solucion_astar is not None else []

        # 6. Skin Base64
        skin_buf = io.BytesIO()
        imagen_completa.save(skin_buf, format='PNG')
        skin_buf.seek(0)
        imagen_skin_base64 = base64.b64encode(skin_buf.getvalue()).decode('utf-8')

        # 7. Respuesta
        return jsonify({
            'estado_inicial_numerico': estado_inicial,
            'imagen_skin_base64': imagen_skin_base64,
            'movimientos_mezcla': movimientos_mezcla,
            'movimientos_solucion': movimientos_solucion,
            'stats_data': {
                'astar': {
                    'movimientos': len(solucion_astar) if solucion_astar else 0,
                    'estados': stats_astar['estados'],
                    'tiempo': round(stats_astar['tiempo'], 4)
                },
                'bfs': {
                    'movimientos': len(solucion_bfs) if solucion_bfs else 0,
                    'estados': stats_bfs['estados'],
                    'tiempo': round(stats_bfs['tiempo'], 4)
                }
            }
        })

    except Exception as e:
        print(f"Error en /solve: {e}") # Log para debugging interno
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
