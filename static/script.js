document.addEventListener('DOMContentLoaded', () => {
    const puzzleForm = document.getElementById('puzzle-form');
    const solveButton = document.getElementById('solve-button');
    const spinner = document.getElementById('spinner');
    const resultsArea = document.getElementById('results-area');
    const mezclasValor = document.getElementById('mezclas-valor');
    const pausaValor = document.getElementById('pausa-valor');
    const mezclasSlider = document.getElementById('mezclas');
    const pausaSlider = document.getElementById('pausa');
    const theoryToggleContainer = document.querySelector('.theory-toggle-container');

    // Switch de algoritmo y etiquetas (para mostrar selección sin aspecto "on/off")
    const algSwitch = document.getElementById('alg-switch');
    const leftAlgLabel = document.querySelector('.algorithm-group .alg-label:first-of-type');
    const rightAlgLabel = document.querySelector('.algorithm-group .alg-label:last-of-type');
    function updateAlgLabels() {
        if (!algSwitch || !leftAlgLabel || !rightAlgLabel) return;
        if (algSwitch.checked) {
            leftAlgLabel.classList.remove('active');
            rightAlgLabel.classList.add('active');
        } else {
            leftAlgLabel.classList.add('active');
            rightAlgLabel.classList.remove('active');
        }
    }
    if (algSwitch) {
        // estado inicial
        updateAlgLabels();
        // actualizar cuando cambie
        algSwitch.addEventListener('change', updateAlgLabels);
    }

    // Actualizar los valores de los sliders en la UI
    if (mezclasSlider && mezclasValor) {
        mezclasSlider.addEventListener('input', () => {
            mezclasValor.textContent = mezclasSlider.value;
        });
    }
    if (pausaSlider && pausaValor) {
        pausaSlider.addEventListener('input', () => {
            pausaValor.textContent = pausaSlider.value;
        });
    }

    puzzleForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevenir la recarga de la página

    // 1. Preparar la reserva de espacio para el bloque de resultados
        resultsArea.innerHTML = '';
        // calcular dimensiones basadas en el ancho del contenedor principal
        const mainEl = document.querySelector('main');
        const mainWidth = mainEl ? mainEl.clientWidth : window.innerWidth;
        // Determinar un ancho fijo para la imagen resultante (consistente entre reserva y render)
        const imageDisplayWidth = Math.min(360, Math.max(220, Math.round(mainWidth * 0.45)));

        // Medir exactamente la altura final que ocupará el bloque de resultados creando
        // un contenedor oculto que imite la estructura final (incluyendo padding/border)
        // y midiendo su offsetHeight. Usamos el ancho del propio `resultsArea` para
        // que la medición sea idéntica en responsive.
        let measuredHeight = 300; // fallback
        try {
            const measRoot = document.createElement('div');
            measRoot.style.position = 'absolute';
            measRoot.style.left = '-9999px';
            measRoot.style.top = '0';
            measRoot.style.visibility = 'hidden';
            measRoot.style.pointerEvents = 'none';
            // usar el ancho real del área de resultados para que coincida con el render final
            const resultsWidth = resultsArea.clientWidth || (document.querySelector('main')?.clientWidth || window.innerWidth);
            measRoot.style.width = resultsWidth + 'px';
            measRoot.style.boxSizing = 'border-box';
            // aplicar padding como el panel final
            measRoot.style.padding = '18px';
            measRoot.style.border = '1px solid transparent';

            // crear el centro con la misma estructura
            const center = document.createElement('div');
            center.className = 'result-center-block';

            const statsContainer = document.createElement('div');
            statsContainer.className = 'stats-container';
            const h3 = document.createElement('h3'); h3.textContent = 'Estadísticas del Proceso:'; statsContainer.appendChild(h3);
            const statsLine = document.createElement('p'); statsLine.className = 'stats-summary'; statsLine.textContent = '0000 • 0.0000s • 0'; statsContainer.appendChild(statsLine);
            center.appendChild(statsContainer);

            const wrapper = document.createElement('div'); wrapper.className = 'image-play-wrapper';
            // image placeholder: square centered
            const imgPlace = document.createElement('div');
            imgPlace.style.width = imageDisplayWidth + 'px';
            imgPlace.style.height = imageDisplayWidth + 'px';
            imgPlace.style.margin = '12px auto';
            imgPlace.style.borderRadius = '6px';
            wrapper.appendChild(imgPlace);
            const btn = document.createElement('button'); btn.className = 'replay-button'; btn.textContent = 'Ver Animación'; wrapper.appendChild(btn);
            center.appendChild(wrapper);

            measRoot.appendChild(center);
            document.body.appendChild(measRoot);
            measuredHeight = Math.ceil(measRoot.offsetHeight);
            document.body.removeChild(measRoot);
            // store measured height so final rendering uses the exact same value
            try { resultsArea.dataset.reservedHeight = String(measuredHeight); } catch(e){}
        } catch(e) { /* fallback retained */ }

        const estimated = measuredHeight;

        // Aplicar la clase reserving y preparar el spinner dentro del panel
        resultsArea.classList.remove('has-content');
        resultsArea.classList.add('reserving');

        // mover spinner al panel y asegurar que ocupa todo el panel para centrarlo
        if (spinner.parentElement !== resultsArea) {
            try { spinner.parentElement && spinner.parentElement.removeChild(spinner); } catch(e){}
            resultsArea.appendChild(spinner);
        }
        spinner.style.display = 'flex';
        spinner.style.width = '100%';
        spinner.style.height = '100%';
        const spinnerInner = spinner.querySelector('.spinner-inner');
        if (spinnerInner) spinnerInner.classList.add('fade-in');

        // Animar min-height de 0 -> estimated para que el botón de teoría se desplace suavemente
        resultsArea.style.setProperty('--reserved-height', '0px');
        // force reflow
        void resultsArea.offsetHeight;
        requestAnimationFrame(() => {
            resultsArea.style.setProperty('--reserved-height', estimated + 'px');
        });

        // Guardar el ancho que usaremos para renderizar la imagen, para que el bloque final
        // coincida exactamente con la medición anterior.
        resultsArea.dataset.reservedImageWidth = imageDisplayWidth;

        solveButton.disabled = true;

        // 2. Crear FormData a partir del formulario
        // Usamos FormData(...) para incluir los campos del form, pero añadimos
        // explícitamente los sliders con los nombres que el backend espera
        // ('cantidad_mezclas' y 'pausa_animacion').
        const formData = new FormData(puzzleForm);
        // Asegurar que los valores de los sliders estén presentes con los nombres esperados
        if (mezclasSlider) {
            formData.set('cantidad_mezclas', mezclasSlider.value);
        }
        if (pausaSlider) {
            // En el backend se lee 'pausa' como float
            formData.set('pausa', pausaSlider.value);
        }

    // Algoritmo: usamos un switch visual. El backend espera 'algoritmo' con 'astar' o 'bfs'.
    const algHidden = document.getElementById('algoritmo-hidden');
    if (algSwitch && algHidden) {
        const alg = algSwitch.checked ? 'bfs' : 'astar';
        algHidden.value = alg;
        formData.set('algoritmo', alg);
    }

        // Actualizar visualmente las etiquetas A*/BFS para que indiquen cuál está seleccionado
        (function updateAlgLabelsOnSubmit(){
            const leftLabel = document.querySelector('.algorithm-group .alg-label:first-of-type');
            const rightLabel = document.querySelector('.algorithm-group .alg-label:last-of-type');
            if (leftLabel && rightLabel && algSwitch) {
                if (algSwitch.checked) {
                    leftLabel.classList.remove('active');
                    rightLabel.classList.add('active');
                } else {
                    leftLabel.classList.add('active');
                    rightLabel.classList.remove('active');
                }
            }
        })();

        // 3. Usar fetch para enviar los datos al backend
        fetch('/solve', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                // Si la respuesta no es OK, intenta leer el JSON de error del backend
                return response.json().then(err => { throw new Error(err.error || 'Error en el servidor') });
            }
            // 4. La respuesta es JSON, leerla como tal
            return response.json();
        })
        .then(data => {
            // Limpiar resultados anteriores
            resultsArea.innerHTML = '';
            // Contenedor centrado que agrupa estadísticas e imagen (para centrar ambos juntos)
            const centerBlock = document.createElement('div');
            centerBlock.className = 'result-center-block';

            // 5. Mostrar estadísticas resumidas usando el objeto estructurado del backend
            (function renderSummary(){
                const summary = (data && data.stats_summary) ? data.stats_summary : null;
                const statsContainer = document.createElement('div');
                statsContainer.className = 'stats-container';
                statsContainer.innerHTML = '<h3>Estadísticas del Proceso:</h3>';

                if (summary) {
                    // Crear línea resumen con iconos y animación
                    const p = document.createElement('p');
                    p.className = 'stats-summary';

                    const parts = [];
                    // SVG icons inline (uses currentColor for contrast)
                    const iconSearch = `
                        <span class="stats-icon" title="Estados explorados" aria-hidden="true">
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="1.5" fill="none"></circle>
                                <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></line>
                            </svg>
                        </span>`;
                    const iconTimer = `
                        <span class="stats-icon" title="Tiempo de búsqueda" aria-hidden="true">
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                <path d="M8 2h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"></path>
                                <circle cx="12" cy="13" r="7" stroke="currentColor" stroke-width="1.5" fill="none"></circle>
                                <path d="M12 10v4l2 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"></path>
                            </svg>
                        </span>`;
                    const iconTarget = `
                        <span class="stats-icon" title="Movimientos para resolver" aria-hidden="true">
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5" fill="none"></circle>
                                <circle cx="12" cy="12" r="6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
                                <circle cx="12" cy="12" r="2" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
                            </svg>
                        </span>`;

                    if (typeof summary.estados_explorados !== 'undefined' && summary.estados_explorados !== null) {
                        parts.push(`<span class="stats-item">${iconSearch} ${summary.estados_explorados}</span>`);
                    }
                    if (typeof summary.tiempo_segundos !== 'undefined' && summary.tiempo_segundos !== null) {
                        parts.push(`<span class="stats-item">${iconTimer} ${summary.tiempo_segundos.toFixed(4)}s</span>`);
                    }
                    if (typeof summary.move_count !== 'undefined' && summary.move_count !== null) {
                        parts.push(`<span class="stats-item">${iconTarget} ${summary.move_count}</span>`);
                    }

                    if (parts.length === 0) {
                        // Fallback: mostrar breve lista compacta de data.stats
                        const fallback = Array.isArray(data.stats) ? data.stats.join(' • ') : '';
                        p.innerHTML = fallback || 'Sin estadísticas disponibles.';
                    } else {
                        p.innerHTML = parts.join(' • ');
                    }

                    statsContainer.appendChild(p);
                    // aplicar fade-in al título y a la línea de resumen
                    const h3 = statsContainer.querySelector('h3');
                    if (h3) h3.classList.add('fade-in');
                    p.classList.add('fade-in');
                } else {
                    // Fallback: mostrar las estadísticas completas si no hay summary
                    const ul = document.createElement('ul');
                    const stats = Array.isArray(data.stats) ? data.stats : [];
                    stats.forEach(s => { const li = document.createElement('li'); li.textContent = s; ul.appendChild(li); });
                    statsContainer.appendChild(ul);
                }

                centerBlock.appendChild(statsContainer);
            })();
            resultsArea.appendChild(centerBlock);

            // Ajustar la altura reservada usando la misma medida que pre-calculamos
            // (evita que el panel se encoja al cambiar de clase)
            setTimeout(() => {
                const stored = parseInt(resultsArea.dataset.reservedHeight, 10);
                const finalHeight = Number.isFinite(stored) ? stored : (centerBlock.offsetHeight || estimated);
                resultsArea.style.setProperty('--reserved-height', finalHeight + 'px');

                // Ocultar y/o remover el spinner dentro del panel
                try {
                    if (spinner && spinner.parentElement === resultsArea) {
                        spinner.style.display = 'none';
                    }
                } catch(e) { /* ignore */ }

                // Marcar que ahora tenemos contenido y limpiar la clase reserving
                resultsArea.classList.add('has-content');
                resultsArea.classList.remove('reserving');
            }, 40);

            // Ya mostramos movimientos dentro del resumen; no añadir párrafo repetitivo.

            // 6. Mostrar la imagen inicial y el botón de "Ver Animación"
            if (data.initial_image_base64 && data.gif_base64 && data.static_image_base64) {
                // Contenedor relativo para superponer imágenes
                const container = document.createElement('div');
                container.style.position = 'relative';
                container.style.display = 'inline-block';

                // Imagen mezclada (inicial) - visible al inicio
                const imgMixed = document.createElement('img');
                imgMixed.src = 'data:image/png;base64,' + data.initial_image_base64;
                imgMixed.id = 'puzzle-image-mixed';
                imgMixed.alt = 'Puzzle mezclado';
                imgMixed.style.display = 'block';
                container.appendChild(imgMixed);

                // Imagen GIF (oculta hasta que se reproduzca) - position absolute para superponer
                const imgGif = document.createElement('img');
                imgGif.id = 'puzzle-image-gif';
                imgGif.alt = 'Animación';
                imgGif.style.display = 'none';
                imgGif.style.position = 'absolute';
                imgGif.style.top = '0';
                imgGif.style.left = '0';
                imgGif.style.width = '100%';
                imgGif.style.height = '100%';
                imgGif.dataset.animatedSrc = 'data:image/gif;base64,' + data.gif_base64;
                container.appendChild(imgGif);

                // Imagen estática final (oculta hasta que termine la animación)
                const imgFinal = document.createElement('img');
                imgFinal.id = 'puzzle-image-final';
                imgFinal.alt = 'Puzzle resuelto';
                imgFinal.src = 'data:image/png;base64,' + data.static_image_base64;
                imgFinal.style.display = 'none';
                imgFinal.style.position = 'absolute';
                imgFinal.style.top = '0';
                imgFinal.style.left = '0';
                imgFinal.style.width = '100%';
                imgFinal.style.height = '100%';
                container.appendChild(imgFinal);

                // Envolver imagen y botón en un contenedor para poder centrar el botón
                const wrapper = document.createElement('div');
                wrapper.className = 'image-play-wrapper';
                // Si existe un ancho reservado, usarlo para que la imagen final coincida con la medición
                const reservedWidth = resultsArea.dataset.reservedImageWidth;
                if (reservedWidth) wrapper.style.width = reservedWidth + 'px';
                wrapper.appendChild(container);

                // Crear el botón de "Ver Animación"
                const replayButton = document.createElement('button');
                replayButton.id = 'replay-button';
                replayButton.className = 'replay-button';
                replayButton.textContent = 'Ver Animación';
                wrapper.appendChild(replayButton);

                // Añadir el wrapper al bloque centrado (imagen + botón)
                centerBlock.appendChild(wrapper);
                // aplicar fade-in a la imagen y al botón
                wrapper.classList.add('fade-in');
                replayButton.classList.add('fade-in');

                // Duración en ms (fallback razonable si no viene)
                const duration = parseInt(data.gif_duration, 10) || (300 * ( (data.gif_frame_count && parseInt(data.gif_frame_count,10)) ||  ( (data.gif_base64||'').length ? Math.max(5, Math.floor((data.gif_base64.length/10000))) : 5) ));

                // Añadir el event listener al botón
                replayButton.addEventListener('click', () => {
                    // Asegurar que el contenedor mantiene tamaño (imgMixed está visible)
                    // No ocultamos imgMixed para evitar que el contenedor colapse.

                    // Preparar capas: mixed (base), final (sobre), gif (tope cuando reproduzca)
                    imgMixed.style.zIndex = '1';
                    imgFinal.style.zIndex = '2';
                    imgGif.style.zIndex = '3';

                    // Forzar reinicio del GIF asignando primero vacío
                    imgGif.src = '';
                    // Pequeña pausa para asegurar que algunos navegadores reinicien el GIF
                    // (aumentado un poco para compatibilidad)
                    setTimeout(() => {
                        imgGif.src = imgGif.dataset.animatedSrc;
                        imgGif.style.display = 'block';
                    }, 50);

                    // Deshabilitar botón durante la animación
                    replayButton.disabled = true;

                    // Ocultamos el GIF ligeramente ANTES de que pueda reiniciarse
                    // para evitar ver el primer fotograma de reinicio.
                    const marginBeforeEnd = 40; // ms
                    const hideAfter = Math.max(0, duration - marginBeforeEnd);

                    // Al terminar la animación, ocultar GIF y mostrar imagen final (sobre la mezclada)
                    setTimeout(() => {
                        imgGif.style.display = 'none';
                        imgFinal.style.display = 'block';
                        replayButton.disabled = false;
                    }, hideAfter);
                });
            }
        })
        .catch(error => {
            // Manejar cualquier error de red o del servidor: mostrar al usuario
            const spinnerInnerErr = spinner.querySelector('.spinner-inner');
            if (spinnerInnerErr) spinnerInnerErr.classList.remove('fade-in');
            spinner.style.display = 'none';
            solveButton.disabled = false;
            resultsArea.innerHTML = `<p style="color:red;">Ocurrió un error: ${error.message}</p>`;
        })
        .finally(() => {
            // 7. Ocultar el spinner y reactivar el botón
            const spinnerInnerFin = spinner.querySelector('.spinner-inner');
            if (spinnerInnerFin) spinnerInnerFin.classList.remove('fade-in');
            spinner.style.display = 'none';
            solveButton.disabled = false;
        });
    });

    // Listener para el botón de reset: limpiar el área de resultados también
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            // Ocultar spinner por si acaso y habilitar el botón de resolver
            spinner.style.display = 'none';
            solveButton.disabled = false;

            // Si no hay contenido, salimos rápidamente
            if (!resultsArea) return;

            try {
                // Primero: desvanecer rápidamente el contenido dentro del panel
                const centerBlock = resultsArea.querySelector('.result-center-block');
                const fadeDuration = 180; // ms, debe coincidir con CSS

                const doCollapse = () => {
                    // Obtener la altura actual del panel como inicio de la animación
                    const currentHeight = resultsArea.offsetHeight || parseInt(resultsArea.dataset.reservedHeight, 10) || 320;

                    // Preparar el panel para la animación de colapso usando la variable
                    // CSS --reserved-height (min-height transition definido en CSS).
                    resultsArea.style.setProperty('--reserved-height', currentHeight + 'px');
                    resultsArea.classList.add('reserving');
                    resultsArea.classList.remove('has-content');

                    // Forzar reflow para establecer el estado inicial
                    void resultsArea.offsetHeight;

                    // Iniciar la animación hacia 0 (colapso)
                    requestAnimationFrame(() => {
                        resultsArea.style.setProperty('--reserved-height', '0px');
                    });

                    // Al terminar la transición, limpiar el DOM y atributos relacionados
                    const onTransitionEnd = (ev) => {
                        // Aceptar transiciones relacionadas con la altura/altura mínima
                        if (ev.propertyName && !(ev.propertyName.includes('height') || ev.propertyName.includes('min-height'))) return;

                        resultsArea.removeEventListener('transitionend', onTransitionEnd);

                        // Limpiar contenido y datos relacionados
                        resultsArea.innerHTML = '';
                        delete resultsArea.dataset.reservedHeight;
                        delete resultsArea.dataset.reservedImageWidth;

                        // Quitar la clase reserving (dejamos el panel colapsado)
                        resultsArea.classList.remove('reserving');

                        // Eliminar la variable inline para no interferir en futuros renders
                        try { resultsArea.style.removeProperty('--reserved-height'); } catch (e){}
                    };

                    resultsArea.addEventListener('transitionend', onTransitionEnd);
                };

                if (centerBlock) {
                    // Añadir clase para desvanecer (CSS maneja la transición de opacidad)
                    centerBlock.classList.add('fade-out');

                    // En caso de que el navegador no dispare transitionend como esperamos,
                    // usar un timeout seguro: primero esperar al fade, luego colapsar.
                    const onFadeEnd = (ev) => {
                        if (ev && ev.propertyName && ev.propertyName !== 'opacity') return;
                        centerBlock.removeEventListener('transitionend', onFadeEnd);
                        doCollapse();
                    };

                    centerBlock.addEventListener('transitionend', onFadeEnd);

                    // Timeout fallback
                    setTimeout(() => {
                        if (centerBlock.classList.contains('fade-out')) {
                            // En caso de que transitionend no haya disparado
                            centerBlock.removeEventListener('transitionend', onFadeEnd);
                            doCollapse();
                        }
                    }, fadeDuration + 60);
                } else {
                    // Si no hay contenido, colapsar inmediatamente
                    doCollapse();
                }

            } catch (e) {
                // Fallback: simplemente vaciar el area si algo falla
                resultsArea.innerHTML = '';
                resultsArea.classList.remove('has-content');
                resultsArea.classList.remove('reserving');
                try { resultsArea.style.removeProperty('--reserved-height'); } catch (err) {}
                console.warn('Error durante la animación de colapso:', e);
            }
        });
    }

    // Listener para alternar la sección teórica (acordeón)
    const toggleTheoryButton = document.getElementById('toggle-theory-button');
    const theorySection = document.getElementById('theory-section');
    if (toggleTheoryButton && theorySection) {
        // prepare for CSS transition
        theorySection.style.overflow = 'hidden';
        theorySection.style.maxHeight = '0';
        theorySection.style.transition = 'max-height 350ms ease, opacity 250ms ease';
        theorySection.style.opacity = '0';

        toggleTheoryButton.addEventListener('click', () => {
            const isOpen = toggleTheoryButton.classList.contains('open');
            if (!isOpen) {
                // open: set maxHeight to scrollHeight for smooth animation
                const h = theorySection.scrollHeight;
                theorySection.style.maxHeight = h + 'px';
                theorySection.style.opacity = '1';
                toggleTheoryButton.classList.add('open');
                toggleTheoryButton.textContent = 'Ocultar Teoría ▲';
            } else {
                // close
                theorySection.style.maxHeight = '0';
                theorySection.style.opacity = '0';
                toggleTheoryButton.classList.remove('open');
                toggleTheoryButton.textContent = 'Ver Explicación Teórica ▼';
            }
        });
        // if content changes (rare), update maxHeight when open
        new ResizeObserver(() => {
            if (toggleTheoryButton.classList.contains('open')) {
                theorySection.style.maxHeight = theorySection.scrollHeight + 'px';
            }
        }).observe(theorySection);
    }

    // Theme toggle: light/dark with persistence
    const themeToggle = document.getElementById('theme-toggle-button');
    const root = document.documentElement;
    function applyTheme(theme) {
        if (theme === 'light') {
            root.setAttribute('data-theme', 'light');
            if (themeToggle) themeToggle.textContent = 'Modo Oscuro';
        } else {
            root.removeAttribute('data-theme');
            if (themeToggle) themeToggle.textContent = 'Modo Claro';
        }
    }

    // load saved theme
    const savedTheme = localStorage.getItem('sliding_puzzle_theme');
    if (savedTheme) applyTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
            const next = current === 'light' ? 'dark' : 'light';
            applyTheme(next);
            localStorage.setItem('sliding_puzzle_theme', next);
        });
    }
});
