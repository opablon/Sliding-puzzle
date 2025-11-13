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

def mezclar_puzzle(estado_objetivo, num_movimientos, semilla_aleatoria, stats_list=None):
    """
    Mezcla el puzzle realizando una caminata aleatoria desde el estado objetivo.
    Evita movimientos que deshacen el movimiento anterior.
    """
    if stats_list is not None:
        stats_list.append("Mezclando piezas...")
    random.seed(semilla_aleatoria)

    estado_actual = estado_objetivo
    ultimo_movimiento = None
    opuestos = {'ARRIBA': 'ABAJO', 'ABAJO': 'ARRIBA', 'IZQUIERDA': 'DERECHA', 'DERECHA': 'IZQUIERDA'}

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

    return estado_actual

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

def resolver_puzzle_bfs(estado_inicial, estado_objetivo, stats_list=None):
    """
    Resuelve el puzzle usando BFS.
    """
    if estado_inicial == estado_objetivo:
        # Ya está resuelto: no se exploraron estados adicionales
        return [], 0

    cola = deque([(estado_inicial, [])])
    visitados = {estado_inicial}

    if stats_list is not None:
        stats_list.append("Buscando solución con BFS...")
    while cola:
        estado_actual, ruta_actual = cola.popleft()
        for nuevo_estado, movimiento in generar_sucesores(estado_actual):
            if nuevo_estado not in visitados:
                visitados.add(nuevo_estado)
                nueva_ruta = ruta_actual + [movimiento]
                if nuevo_estado == estado_objetivo:
                    if stats_list is not None:
                        stats_list.append(f"Solución encontrada. Estados explorados: {len(visitados)}")
                    return nueva_ruta, len(visitados)
                cola.append((nuevo_estado, nueva_ruta))
                if len(visitados) % 5000 == 0:
                    if stats_list is not None:
                        stats_list.append(f"Estados explorados: {len(visitados)}...")
    # No se encontró solución dentro del espacio explorado
    return None, len(visitados)

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

def resolver_puzzle_a_estrella(estado_inicial, estado_objetivo, mapa_objetivo, stats_list=None):
    """
    Resuelve el puzzle usando A* y la heurística de Manhattan.
    Utiliza un mapa de objetivos pre-calculado para mayor eficiencia.
    """
    if estado_inicial == estado_objetivo:
        return []

    costo_g_inicial = 0
    costo_total_inicial = costo_g_inicial + heuristica_manhattan(estado_inicial, mapa_objetivo)

    contador = 0
    frontera = [
        (costo_total_inicial, contador, costo_g_inicial, estado_inicial, [])
    ]
    costo_g_registrado = {estado_inicial: costo_g_inicial}

    if stats_list is not None:
        stats_list.append("Buscando solución con A*...")
    while frontera:
        _, _, costo_g_actual, estado_actual, ruta_actual = heapq.heappop(frontera)

        if estado_actual == estado_objetivo:
            if stats_list is not None:
                stats_list.append(f"Solución encontrada. Estados explorados: {len(costo_g_registrado)}")
            return ruta_actual, len(costo_g_registrado)

        if costo_g_actual > costo_g_registrado.get(estado_actual, float('inf')):
            continue

        for nuevo_estado, movimiento in generar_sucesores(estado_actual):
            nuevo_costo_g = costo_g_actual + 1
            if nuevo_costo_g < costo_g_registrado.get(nuevo_estado, float('inf')):
                costo_g_registrado[nuevo_estado] = nuevo_costo_g
                nuevo_costo_total = nuevo_costo_g + heuristica_manhattan(nuevo_estado, mapa_objetivo)
                contador += 1
                heapq.heappush(frontera, (nuevo_costo_total, contador, nuevo_costo_g, nuevo_estado, ruta_actual + [movimiento]))

                if len(costo_g_registrado) % 5000 == 0:
                    if stats_list is not None:
                        stats_list.append(f"Estados explorados (A*): {len(costo_g_registrado)}...")
    # No se encontró solución
    return None, len(costo_g_registrado)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    """
    Endpoint para resolver el puzzle. Lee el formulario y archivo enviado,
    fuerza tamaño 3x3 (TAMANO_PUZZLE=3), mezcla según semilla/mezclas,
    resuelve con A* o BFS, genera un GIF en memoria y lo devuelve.
    """
    stats = []
    # Forzamos 3x3 para la demo rápida
    TAMANO_PUZZLE = 3
    REDIMENSION_IMAGEN = (300, 300)

    # Fuente de la imagen: preferir archivo subido, si no usar URL
    uploaded_file = request.files.get('imagen')
    image_url = (request.form.get('image-url') or '').strip()

    # Determinar qué usar
    if uploaded_file and getattr(uploaded_file, 'filename', ''):
        imagen_fuente = uploaded_file
        stats.append("Usando imagen subida por el usuario.")
    elif image_url:
        imagen_fuente = image_url
        stats.append(f"Usando URL de imagen: {image_url}")
    else:
        return jsonify({'error': 'No se proporcionó ninguna imagen (archivo o URL)'}), 400

    # Cargar y dividir imagen en piezas
    try:
        stats.append("Cargando y procesando imagen...")
        _, lista_piezas, tamano_pieza = cargar_imagen(imagen_fuente, TAMANO_PUZZLE, REDIMENSION_IMAGEN)
    except Exception as e:
        # Incluir información en stats para facilitar debugging
        stats.append(f"Error al procesar la imagen: {e}")
        return jsonify({'error': f'Error al procesar la imagen: {e}', 'stats': stats}), 400

    # Crear mapas y estado objetivo
    stats.append("Creando estados del puzzle...")
    mapa_piezas, mapa_objetivo, estado_objetivo = crear_mapas_y_estados(TAMANO_PUZZLE, lista_piezas, tamano_pieza)

    # Semilla, número de mezclas y pausa de animación
    semilla = request.form.get('semilla', '')
    try:
        semilla_int = int(semilla) if semilla != '' else None
    except ValueError:
        semilla_int = None

    try:
        num_mezclas = int(request.form.get('cantidad_mezclas', 30))
    except (ValueError, TypeError):
        num_mezclas = 30
    try:
        pausa = float(request.form.get('pausa', 0.3))
    except (ValueError, TypeError):
        pausa = 0.3

    # Mezclar
    estado_mezclado = mezclar_puzzle(estado_objetivo, num_mezclas, semilla_int, stats)

    # Generar imagen inicial (mezclada)
    img_inicial = construir_estado_imagen(estado_mezclado, mapa_piezas, tamano_pieza)
    initial_buf = io.BytesIO()
    img_inicial.save(initial_buf, format='PNG')
    initial_buf.seek(0)
    initial_image_base64 = base64.b64encode(initial_buf.getvalue()).decode('utf-8')

    # Elegir algoritmo
    algoritmo = (request.form.get('algoritmo') or 'astar').lower()
    start = time.time()
    if 'bfs' in algoritmo:
        solucion, estados_explorados = resolver_puzzle_bfs(estado_mezclado, estado_objetivo, stats)
    else:
        solucion, estados_explorados = resolver_puzzle_a_estrella(estado_mezclado, estado_objetivo, mapa_objetivo, stats)
    elapsed = time.time() - start
    stats.append(f"Tiempo de búsqueda: {elapsed:.4f} segundos.")

    # Agregar resumen estructurado que el frontend puede consumir directamente
    stats_summary = {
        'estados_explorados': int(estados_explorados) if 'estados_explorados' in locals() else None,
        'tiempo_segundos': float(elapsed),
        # move_count se calcula más abajo
    }

    if solucion is None:
        stats.append("No se encontró solución.")

    # Generar frames a partir del estado mezclado y la solución (si existe)
    frames = []
    estado_actual = estado_mezclado
    frames.append(construir_estado_imagen(estado_actual, mapa_piezas, tamano_pieza))

    if solucion:
        for movimiento in solucion:
            estado_actual = aplicar_movimiento(estado_actual, movimiento)
            frames.append(construir_estado_imagen(estado_actual, mapa_piezas, tamano_pieza))

    # Guardar GIF en memoria
    gif_buf = io.BytesIO()
    try:
        if len(frames) == 1:
            frames[0].save(gif_buf, format='GIF')
        else:
            # loop=1 para pedir que se reproduzca una sola vez (Pillow interpreta loop como
            # el número de repeticiones; en la práctica también controlamos con JS)
            frames[0].save(gif_buf, format='GIF', save_all=True, append_images=frames[1:], duration=int(pausa * 1000), loop=1)
    except Exception as e:
        return jsonify({'error': f'Error al generar GIF: {e}'}), 500

    gif_buf.seek(0)

    # Convertir GIF a Base64
    gif_base64 = base64.b64encode(gif_buf.getvalue()).decode('utf-8')
    # Generar imagen estática final (estado objetivo)
    img_resuelta = construir_estado_imagen(estado_objetivo, mapa_piezas, tamano_pieza)
    static_buf = io.BytesIO()
    img_resuelta.save(static_buf, format='PNG')
    static_buf.seek(0)
    static_image_base64 = base64.b64encode(static_buf.getvalue()).decode('utf-8')

    # Calcular duración total aproximada del GIF (ms)
    duracion_por_frame = pausa * 1000
    gif_duration = (len(solucion) + 1) * duracion_por_frame if solucion else duracion_por_frame
    # Número de movimientos de la solución
    move_count = len(solucion) if solucion else 0
    stats_summary['move_count'] = move_count

    # Devolver JSON con stats, GIF, la imagen inicial y la imagen final + duración
    return jsonify({
        'stats': stats,
        'stats_summary': stats_summary,
        'gif_base64': gif_base64,
        'initial_image_base64': initial_image_base64,
        'static_image_base64': static_image_base64,
        'gif_duration': gif_duration,
        'gif_frame_count': len(frames),
        'move_count': move_count
    })

if __name__ == '__main__':
    app.run(debug=True)
