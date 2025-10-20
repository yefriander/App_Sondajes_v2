// Variables globales
const selectProyecto = document.getElementById('select-proyecto');
const selectSondaje = document.getElementById('select-sondaje');
const btnCargarRegistros = document.getElementById('btn-cargar-registros');
const btnProcesarTodos = document.getElementById('btn-procesar-todos');
const btnDescargarZip = document.getElementById('btn-descargar-zip');
const btnDescargarZipInfo = document.getElementById('btn-descargar-zip-info');
const btnGenerarReporte = document.getElementById('btn-generar-reporte');
const inputLogo = document.getElementById('input-logo');
const selectTipoInforme = document.getElementById('select-tipo-informe');
const mensajeReporte = document.getElementById('mensaje-reporte');
const divResultados = document.getElementById('resultados');
const galeriaImagenes = document.getElementById('galeria-imagenes');
const contenedorImagenes = document.getElementById('contenedor-imagenes');

let registrosActuales = [];
let codigoProyectoActual = '';
let holeIdActual = '';
let idSondajeActual = '';
let procesandoTodos = false;
let imagenesData = [];
let logoSubido = null;

// Evento: Cambio de proyecto
selectProyecto.addEventListener('change', async function() {
    const codigoProyecto = this.value;
    
    selectSondaje.innerHTML = '<option value="">-- Cargando sondajes... --</option>';
    selectSondaje.disabled = true;
    btnCargarRegistros.disabled = true;
    btnProcesarTodos.style.display = 'none';
    divResultados.innerHTML = '';
    galeriaImagenes.style.display = 'none';
    
    if (!codigoProyecto) {
        selectSondaje.innerHTML = '<option value="">-- Primero seleccione un proyecto --</option>';
        return;
    }
    
    try {
        const response = await fetch(`/api/sondajes/${codigoProyecto}/`);
        const data = await response.json();
        
        if (data.success && data.sondajes.length > 0) {
            selectSondaje.innerHTML = '<option value="">-- Seleccione un sondaje --</option>';
            
            data.sondajes.forEach(sondaje => {
                const option = document.createElement('option');
                option.value = sondaje.id_sondaje_proyecto;
                option.textContent = sondaje.hole_id;
                selectSondaje.appendChild(option);
            });
            
            selectSondaje.disabled = false;
        } else {
            selectSondaje.innerHTML = '<option value="">-- No hay sondajes disponibles --</option>';
        }
    } catch (error) {
        console.error('Error al cargar sondajes:', error);
        selectSondaje.innerHTML = '<option value="">-- Error al cargar sondajes --</option>';
    }
});

// Evento: Cambio de sondaje
selectSondaje.addEventListener('change', function() {
    const idSondaje = this.value;
    btnCargarRegistros.disabled = !idSondaje || procesandoTodos;
    btnProcesarTodos.style.display = 'none';
    divResultados.innerHTML = '';
    galeriaImagenes.style.display = 'none';
});

// Evento: Cargar registros
btnCargarRegistros.addEventListener('click', async function() {
    const idSondaje = selectSondaje.value;
    
    if (!idSondaje) return;
    
    divResultados.innerHTML = '<p style="text-align: center;">⏳ Cargando registros...</p>';
    divResultados.style.display = 'block';
    galeriaImagenes.style.display = 'none';
    
    try {
        const response = await fetch(`/api/registros/${idSondaje}/`);
        divResultados.style.display = 'block';
        const data = await response.json();
        
        if (data.success && data.registros.length > 0) {
            codigoProyectoActual = selectProyecto.value;
            holeIdActual = selectSondaje.options[selectSondaje.selectedIndex].text;
            idSondajeActual = selectSondaje.value;
            registrosActuales = data.registros;
            
            // Contar registros sin procesar
            const registrosSinProcesar = data.registros.filter(r => !r.procesado);
            const registrosProcesados = data.registros.length - registrosSinProcesar.length;
            
            if (registrosSinProcesar.length > 0) {
                // Hay registros pendientes - mostrar resumen
                divResultados.innerHTML = `
                    <div class="registros-pendientes">
                        <h3 style="color: #227FF2; margin-bottom: 15px;">📊 Resumen de Registros</h3>
                        <div style="display: inline-block; text-align: left; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <p style="margin: 10px 0; font-size: 18px;"><strong>Total de registros:</strong> ${data.registros.length}</p>
                            <p style="margin: 10px 0; font-size: 18px; color: #28a745;"><strong>✅ Ya procesados:</strong> ${registrosProcesados}</p>
                            <p style="margin: 10px 0; font-size: 18px; color: #dc3545;"><strong>⏳ Pendientes:</strong> ${registrosSinProcesar.length}</p>
                        </div>
                        <p style="margin-top: 20px; color: #666;">Haz clic en "Procesar Todos" para iniciar el procesamiento automático.</p>
                    </div>
                `;
                
                btnProcesarTodos.style.display = 'inline-block';
                btnProcesarTodos.textContent = `Procesar Todos (${registrosSinProcesar.length} pendientes)`;
            } else {
                // Todos procesados - cargar imágenes automáticamente
                divResultados.innerHTML = `
                    <div class="cargar-imagenes-procesadas">
                        <h3 style="color: black; margin-bottom: 10px;">✅ Todos los registros están procesados</h3>
                        <p style="color: black; margin: 0;">Total de registros: ${data.registros.length}</p>
                        <p style="color: black; margin-top: 10px;">⏳ Cargando imágenes...</p>
                    </div>
                `;
                btnProcesarTodos.style.display = 'none';
                
                // Cargar imágenes automáticamente
                await cargarImagenes(idSondaje);
            }
            
        } else {
            divResultados.innerHTML = `
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">
                    <p style="margin: 0;">No se encontraron registros para este sondaje.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error al cargar registros:', error);
        divResultados.innerHTML = `
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #dc3545;">
                <p style="margin: 0; color: #721c24;">Error al cargar los registros. Por favor, intente nuevamente.</p>
            </div>
        `;
    }
});

// FUNCIÓN: Cargar y mostrar imágenes procesadas
async function cargarImagenes(idSondaje) {
    try {
        console.log('📷 Cargando imágenes procesadas...');
        
        const response = await fetch(`/api/imagenes-procesadas/${idSondaje}/`);
        const data = await response.json();
        
        if (data.success && data.imagenes.length > 0) {
            imagenesData = data.imagenes;
            
            // Ocultar resultados y mostrar galería
            divResultados.style.display = 'none';
            galeriaImagenes.style.display = 'block';
            
            // Limpiar contenedor
            contenedorImagenes.innerHTML = '';
            
            // Crear tarjetas de imágenes
            imagenesData.forEach((item, index) => {
                const card = crearTarjetaImagen(item, index);
                contenedorImagenes.appendChild(card);
            });

            // Imprimir las imagenes cargadas
            console.log(`✅ ${imagenesData.length} imágenes cargadas`);

            // Validar si se puede generar reporte
            validarReporte();
            
            console.log(`✅ ${imagenesData.length} imágenes cargadas`);
        } else {
            divResultados.innerHTML = `
                <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #dc3545;">
                    <p style="margin: 0; color: #721c24;">No se encontraron imágenes procesadas para este sondaje.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error al cargar imágenes:', error);
        divResultados.innerHTML = `
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #dc3545;">
                <p style="margin: 0; color: #721c24;">Error al cargar las imágenes. Por favor, intente nuevamente.</p>
            </div>
        `;
    }
}

// FUNCIÓN: Validar si se puede generar reporte
function validarReporte() {
    const tieneImagen = imagenesData.length > 0;
    const tieneLogo = logoSubido !== null;
    const tieneTipoInforme = selectTipoInforme.value !== '';
    
    if (tieneImagen && tieneLogo && tieneTipoInforme) {
        btnGenerarReporte.disabled = false;
        btnGenerarReporte.style.cursor = 'pointer';
        btnGenerarReporte.style.opacity = '1';
        mensajeReporte.style.display = 'none';
    } else {
        btnGenerarReporte.disabled = true;
        btnGenerarReporte.style.cursor = 'not-allowed';
        btnGenerarReporte.style.opacity = '0.5';
        
        // Mostrar mensaje de qué falta
        let mensajes = [];
        if (!tieneLogo) mensajes.push('Sube un logo');
        if (!tieneTipoInforme) mensajes.push('Selecciona tipo de informe');
        
        if (mensajes.length > 0) {
            mensajeReporte.style.display = 'block';
            mensajeReporte.style.background = '#fff3cd';
            mensajeReporte.style.color = '#856404';
            mensajeReporte.style.borderLeft = '4px solid #ffc107';
            mensajeReporte.innerHTML = `⚠️ Para generar reporte: ${mensajes.join(', ')}`;
        }
    }
}

// EVENTO: Cambio de logo
inputLogo.addEventListener('change', function(e) {
    const file = e.target.files[0];
    
    if (file) {
        // Validar tamaño (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            alert('⚠️ El logo debe pesar menos de 2MB');
            this.value = '';
            logoSubido = null;
            validarReporte();
            return;
        }
        
        // Validar tipo
        if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
            alert('⚠️ Solo se permiten imágenes PNG o JPG');
            this.value = '';
            logoSubido = null;
            validarReporte();
            return;
        }
        
        logoSubido = file;
        console.log('✅ Logo cargado:', file.name);
        validarReporte();
    } else {
        logoSubido = null;
        validarReporte();
    }
});

// EVENTO: Cambio de tipo de informe
selectTipoInforme.addEventListener('change', function() {
    validarReporte();
});

// FUNCIÓN: Crear tarjeta de imagen
function crearTarjetaImagen(item, index) {
    const card = document.createElement('div');
    card.className = 'imagen-card';
    card.id = `card-${index}`;
    card.style.cssText = 'background: white; border: 2px solid #ddd; border-radius: 8px; padding: 15px; transition: all 0.3s;';
    
    // Estado: imagen activa (1 o 2)
    let imagenActiva = 1;
    
    card.innerHTML = `
        <div style="margin-bottom: 10px;">
            <span style="font-weight: bold; color: #227FF2;">From ${item.from}m - To ${item.to}m</span>
        </div>
        
        <!-- Contenedor de imagen -->
        <div style="position: relative; width: 100%; height: 250px; background: #f5f5f5; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
            ${item.imagen1.url ? `
                <img id="img-${index}-1" src="${item.imagen1.url}" style="width: 100%; height: 100%; object-fit: contain; display: block;" alt="Imagen 1" />
            ` : `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999;">
                    ⚠️ Imagen 1 no disponible
                </div>
            `}
            ${item.imagen2.url ? `
                <img id="img-${index}-2" src="${item.imagen2.url}" style="width: 100%; height: 100%; object-fit: contain; display: none;" alt="Imagen 2" />
            ` : ''}
        </div>
        
        <!-- Botones de toggle -->
        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
            <button id="btn-${index}-1" class="btn-imagen" onclick="cambiarImagen(${index}, 1)" style="flex: 1; padding: 8px; border: 2px solid #227FF2; background: #227FF2; color: white; border-radius: 4px; cursor: pointer; font-weight: bold;">
                Imagen 1
            </button>
            <button id="btn-${index}-2" class="btn-imagen" onclick="cambiarImagen(${index}, 2)" style="flex: 1; padding: 8px; border: 2px solid #ddd; background: white; color: #666; border-radius: 4px; cursor: pointer;">
                Imagen 2
            </button>
        </div>
        
        <!-- Indicador de selección -->
        <div style="text-align: center; color: #28a745; font-size: 12px;">
            ✅ <span id="seleccion-${index}">Imagen 1 seleccionada</span>
        </div>
    `;
    
    return card;
}

// FUNCIÓN GLOBAL: Cambiar imagen activa
window.cambiarImagen = function(index, numeroImagen) {
    const item = imagenesData[index];
    
    // Verificar que la imagen existe
    if (numeroImagen === 2 && !item.imagen2.url) {
        alert('⚠️ La imagen 2 no está disponible');
        return;
    }
    
    // Actualizar visualización
    const img1 = document.getElementById(`img-${index}-1`);
    const img2 = document.getElementById(`img-${index}-2`);
    const btn1 = document.getElementById(`btn-${index}-1`);
    const btn2 = document.getElementById(`btn-${index}-2`);
    const seleccion = document.getElementById(`seleccion-${index}`);
    
    if (numeroImagen === 1) {
        if (img1) img1.style.display = 'block';
        if (img2) img2.style.display = 'none';
        
        btn1.style.background = '#227FF2';
        btn1.style.color = 'white';
        btn1.style.borderColor = '#227FF2';
        btn1.style.fontWeight = 'bold';
        
        btn2.style.background = 'white';
        btn2.style.color = '#666';
        btn2.style.borderColor = '#ddd';
        btn2.style.fontWeight = 'normal';
        
        seleccion.textContent = 'Imagen 1 seleccionada';
        
        // Actualizar estado
        imagenesData[index].imagenSeleccionada = 1;
    } else {
        if (img1) img1.style.display = 'none';
        if (img2) img2.style.display = 'block';
        
        btn2.style.background = '#227FF2';
        btn2.style.color = 'white';
        btn2.style.borderColor = '#227FF2';
        btn2.style.fontWeight = 'bold';
        
        btn1.style.background = 'white';
        btn1.style.color = '#666';
        btn1.style.borderColor = '#ddd';
        btn1.style.fontWeight = 'normal';
        
        seleccion.textContent = 'Imagen 2 seleccionada';
        
        // Actualizar estado
        imagenesData[index].imagenSeleccionada = 2;
    }
};

// EVENTO: Descargar ZIP
btnDescargarZip.addEventListener('click', async function() {
    try {
        // Recopilar imágenes seleccionadas
        const imagenesSeleccionadas = [];
        
        imagenesData.forEach((item, index) => {
            const imagenSeleccionada = item.imagenSeleccionada || 1; // Por defecto imagen 1
            
            if (imagenSeleccionada === 1 && item.imagen1.path) {
                imagenesSeleccionadas.push(item.imagen1.path);
            } else if (imagenSeleccionada === 2 && item.imagen2.path) {
                imagenesSeleccionadas.push(item.imagen2.path);
            }
        });
        
        if (imagenesSeleccionadas.length === 0) {
            alert('⚠️ No hay imágenes seleccionadas para descargar');
            return;
        }
        
        console.log(`📦 Preparando descarga de ${imagenesSeleccionadas.length} imágenes...`);
        
        // Deshabilitar botón
        this.disabled = true;
        this.textContent = 'Preparando descarga...';
        
        // Hacer petición POST
        const response = await fetch('/api/descargar-zip/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                imagenes: imagenesSeleccionadas
            })
        });
        
        if (response.ok) {
            // Descargar archivo
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `imagenes_cajas_${idSondajeActual}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('✅ Descarga completada');
            alert(`✅ Se descargaron ${imagenesSeleccionadas.length} imágenes exitosamente`);
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.error}`);
        }
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = 'Descargar Imágenes Seleccionadas (ZIP)';
        
    } catch (error) {
        console.error('Error al descargar ZIP:', error);
        alert('❌ Error al preparar la descarga. Intente nuevamente.');
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = 'Descargar Imágenes Seleccionadas (ZIP)';
    }
});

// EVENTO: Descargar ZIP con Info
btnDescargarZipInfo.addEventListener('click', async function() {
    try {
        // Recopilar imágenes seleccionadas (misma lógica pero carpeta diferente)
        const imagenesSeleccionadas = [];
        
        imagenesData.forEach((item, index) => {
            const imagenSeleccionada = item.imagenSeleccionada || 1; // Por defecto imagen 1
            
            if (imagenSeleccionada === 1 && item.imagen1.path) {
                // Cambiar ruta de Caja_Sondaje_ a Info_Caja_Sondaje_
                const pathInfo = item.imagen1.path.replace('/Caja_Sondaje_', '/Info_Caja_Sondaje_');
                imagenesSeleccionadas.push(pathInfo);
            } else if (imagenSeleccionada === 2 && item.imagen2.path) {
                // Cambiar ruta de Caja_Sondaje_ a Info_Caja_Sondaje_
                const pathInfo = item.imagen2.path.replace('/Caja_Sondaje_', '/Info_Caja_Sondaje_');
                imagenesSeleccionadas.push(pathInfo);
            }
        });
        
        if (imagenesSeleccionadas.length === 0) {
            alert('⚠️ No hay imágenes seleccionadas para descargar');
            return;
        }
        
        console.log(`📦 Preparando descarga de ${imagenesSeleccionadas.length} imágenes con info...`);
        
        // Deshabilitar botón
        this.disabled = true;
        this.textContent = 'Preparando descarga...';
        
        // Hacer petición POST (misma API)
        const response = await fetch('/api/descargar-zip/', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                imagenes: imagenesSeleccionadas
            })
        });
        
        if (response.ok) {
            // Descargar archivo
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `imagenes_info_${idSondajeActual}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('✅ Descarga completada');
            alert(`✅ Se descargaron ${imagenesSeleccionadas.length} imágenes con info exitosamente`);
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.error}`);
        }
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = 'Descargar Imágenes con Info Seleccionadas (ZIP)';
        
    } catch (error) {
        console.error('Error al descargar ZIP con info:', error);
        alert('❌ Error al preparar la descarga. Intente nuevamente.');
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = 'Descargar Imágenes con Info Seleccionadas (ZIP)';
    }
});

// FUNCIÓN: Procesar un registro individual
async function procesarRegistro(idRegistro) {
    try {
        const response = await fetch('/api/procesar-imagenes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                id_registro: idRegistro,
                codigo_proyecto: codigoProyectoActual,
                hole_id: holeIdActual,
                id_sondaje: idSondajeActual
            })
        });
        
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text();
            console.error('Respuesta del servidor (no es JSON):', text);
            return { success: false, error: 'Respuesta inválida del servidor' };
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Error al procesar registro:', error);
        return { success: false, error: error.message };
    }
}

// EVENTO: Procesar todos los registros
btnProcesarTodos.addEventListener('click', async function() {
    // Deshabilitar botones
    this.disabled = true;
    btnCargarRegistros.disabled = true;
    procesandoTodos = true;
    
    // Obtener registros sin procesar
    const registrosSinProcesar = registrosActuales.filter(r => !r.procesado);
    const total = registrosSinProcesar.length;
    let procesados = 0;
    let exitosos = 0;
    let fallidos = 0;
    
    console.log(`🚀 Iniciando procesamiento de ${total} registros...`);
    
    // Crear barra de progreso
    divResultados.innerHTML = `
        <div style="background: #F2F2F2; padding: 20px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="text-align: center;">⚙️ Procesando Imágenes con YOLO</h3>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span id="progreso-texto" style="font-weight: bold; color: #333;">Procesando registro 0 de ${total}...</span>
                    <span id="progreso-porcentaje" style="font-weight: bold; color: black;">0%</span>
                </div>
                
                <!-- Barra de progreso -->
                <div style="width: 100%; height: 30px; background: #e9ecef; border-radius: 15px; overflow: hidden; position: relative;">
                    <div id="barra-progreso" style="width: 0%; height: 100%; background: linear-gradient(90deg, #F27222, #ffaa33); transition: width 0.3s ease;"></div>
                </div>
            </div>
            
            <!-- Estadísticas -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 20px;">
                <div style="text-align: center; padding: 15px; background: white; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: black;" id="stat-total">${total}</div>
                    <div style="color: #666; margin-top: 5px;">Total</div>
                </div>
                <div style="text-align: center; padding: 15px; background: #F27222; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: white;" id="stat-exitosos">0</div>
                    <div style="color: white; margin-top: 5px;">Exitosos</div>
                </div>
                <div style="text-align: center; padding: 15px; background: grey; border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: white;" id="stat-fallidos">0</div>
                    <div style="color: white; margin-top: 5px;">Fallidos</div>
                </div>
            </div>
            
            <!-- Log de procesamiento -->
            <div style="margin-top: 20px; max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px;" id="log-procesamiento">
                <div style="color: #28a745;">Iniciando procesamiento...</div>
            </div>
        </div>
    `;
    
    const barraProgreso = document.getElementById('barra-progreso');
    const progresoTexto = document.getElementById('progreso-texto');
    const progresoPorcentaje = document.getElementById('progreso-porcentaje');
    const statExitosos = document.getElementById('stat-exitosos');
    const statFallidos = document.getElementById('stat-fallidos');
    const logProcesamiento = document.getElementById('log-procesamiento');
    
    // Función para agregar mensaje al log
    function agregarLog(mensaje, tipo = 'info') {
        const colores = {
            'info': '#227FF2',
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107'
        };
        const div = document.createElement('div');
        div.style.color = colores[tipo] || '#333';
        div.style.marginTop = '5px';
        div.textContent = mensaje;
        logProcesamiento.appendChild(div);
        logProcesamiento.scrollTop = logProcesamiento.scrollHeight;
    }
    
    // Procesar cada registro
    for (let i = 0; i < registrosSinProcesar.length; i++) {
        const registro = registrosSinProcesar[i];
        const numeroActual = i + 1;
        
        // Actualizar UI
        progresoTexto.textContent = `Procesando registro ${numeroActual} de ${total}...`;
        const porcentaje = Math.round((numeroActual / total) * 100);
        progresoPorcentaje.textContent = `${porcentaje}%`;
        barraProgreso.style.width = `${porcentaje}%`;
        
        agregarLog(`⏳ [${numeroActual}/${total}] Procesando registro ID ${registro.id}...`, 'info');
        
        // Procesar
        const resultado = await procesarRegistro(registro.id);
        
        procesados++;
        
        if (resultado.success) {
            exitosos++;
            statExitosos.textContent = exitosos;
            agregarLog(`✅ [${numeroActual}/${total}] Registro ID ${registro.id} procesado exitosamente`, 'success');
            
            // Actualizar el registro en el array
            const idx = registrosActuales.findIndex(r => r.id === registro.id);
            if (idx !== -1) registrosActuales[idx].procesado = true;
        } else {
            fallidos++;
            statFallidos.textContent = fallidos;
            agregarLog(`❌ [${numeroActual}/${total}] Error en registro ID ${registro.id}: ${resultado.error}`, 'error');
        }
        
        // Pausa entre registros
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Finalizado
    console.log(`✅ Procesamiento completado: ${exitosos} exitosos, ${fallidos} fallidos de ${total} totales`);
    agregarLog(`\n🎉 Procesamiento completado!`, 'success');
    agregarLog(`📊 Resultados: ${exitosos} exitosos, ${fallidos} fallidos de ${total} totales`, 'info');
    
    // Esperar 2 segundos y luego cargar imágenes
    setTimeout(async () => {
        divResultados.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <h2 style="color: black; margin-bottom: 20px;">Procesamiento Completado</h2>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0;">
                    <div style="padding: 20px; background: white; border-radius: 8px;">
                        <div style="font-size: 36px; font-weight: bold; color: black;">${total}</div>
                        <div style="color: #666; margin-top: 10px;">Total Procesados</div>
                    </div>
                    <div style="padding: 20px; background: #F27222; border-radius: 8px;">
                        <div style="font-size: 36px; font-weight: bold; color: white;">${exitosos}</div>
                        <div style="color: white; margin-top: 10px;">Exitosos</div>
                    </div>
                    <div style="padding: 20px; background: gray; border-radius: 8px;">
                        <div style="font-size: 36px; font-weight: bold; color: white;">${fallidos}</div>
                        <div style="color: white; margin-top: 10px;">Fallidos</div>
                    </div>
                </div>
                
                <p style="color: #666; font-size: 16px; margin-top: 20px;">⏳ Cargando imágenes procesadas...</p>
            </div>
        `;
        
        // Rehabilitar botones
        btnCargarRegistros.disabled = false;
        btnProcesarTodos.disabled = false;
        procesandoTodos = false;
        btnProcesarTodos.style.display = 'none';
        
        // Cargar imágenes automáticamente
        await cargarImagenes(idSondajeActual);
    }, 2000);
});

// Función auxiliar para obtener CSRF token
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    
    if (!cookieValue) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            cookieValue = csrfInput.value;
        }
    }
    
    return cookieValue;
}

function getCookie(name) {
    if (name === 'csrftoken') {
        return getCSRFToken();
    }
    return null;
}

// Variables globales (agregar esta)
const checkboxGenerarDocx = document.getElementById('checkbox-generar-docx');

// EVENTO: Generar Reporte
btnGenerarReporte.addEventListener('click', async function() {
    try {
        if (!logoSubido) {
            alert('⚠️ Debes subir un logo primero');
            return;
        }
        
        if (!selectTipoInforme.value) {
            alert('⚠️ Debes seleccionar un tipo de informe');
            return;
        }
        
        // Recopilar imágenes seleccionadas
        const imagenesSeleccionadas = [];
        
        imagenesData.forEach((item, index) => {
            const imagenSeleccionada = item.imagenSeleccionada || 1;
            
            if (imagenSeleccionada === 1 && item.imagen1.path) {
                imagenesSeleccionadas.push({
                    path: item.imagen1.path,
                    from: item.from,
                    to: item.to,
                    numero: index + 1
                });
            } else if (imagenSeleccionada === 2 && item.imagen2.path) {
                imagenesSeleccionadas.push({
                    path: item.imagen2.path,
                    from: item.from,
                    to: item.to,
                    numero: index + 1
                });
            }
        });
        
        if (imagenesSeleccionadas.length === 0) {
            alert('⚠️ No hay imágenes seleccionadas');
            return;
        }
        
        const incluirDocx = checkboxGenerarDocx.checked;
        const formatos = incluirDocx ? 'PDF + DOCX' : 'PDF';
        
        console.log(`📄 Generando reporte (${formatos}) con ${imagenesSeleccionadas.length} imágenes...`);
        
        // Deshabilitar botón
        this.disabled = true;
        this.textContent = `⏳ Generando ${formatos}...`;
        
        mensajeReporte.style.display = 'block';
        mensajeReporte.style.background = '#d1ecf1';
        mensajeReporte.style.color = '#0c5460';
        mensajeReporte.style.borderLeft = '4px solid #17a2b8';
        mensajeReporte.innerHTML = `⏳ Procesando ${imagenesSeleccionadas.length} imágenes... Generando ${formatos}`;
        
        // Crear FormData
        const formData = new FormData();
        formData.append('logo', logoSubido);
        formData.append('tipo_informe', selectTipoInforme.value);
        formData.append('id_sondaje', idSondajeActual);
        formData.append('imagenes', JSON.stringify(imagenesSeleccionadas));
        formData.append('generar_docx', incluirDocx ? 'true' : 'false');
        
        // Hacer petición POST
        const response = await fetch('/api/generar-reporte/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Determinar nombre del archivo según formato
            if (incluirDocx) {
                a.download = `reporte_${holeIdActual}_${selectTipoInforme.value}cm.zip`;
            } else {
                a.download = `reporte_${holeIdActual}_${selectTipoInforme.value}cm.pdf`;
            }
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log(`✅ Reporte ${formatos} descargado`);
            
            mensajeReporte.style.display = 'block';
            mensajeReporte.style.background = '#d4edda';
            mensajeReporte.style.color = '#155724';
            mensajeReporte.style.borderLeft = '4px solid #28a745';
            mensajeReporte.innerHTML = `✅ Reporte ${formatos} generado exitosamente`;
            
            setTimeout(() => {
                mensajeReporte.style.display = 'none';
            }, 5000);
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.error}`);
            
            mensajeReporte.style.display = 'none';
        }
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = '📄 Generar Reporte';
        validarReporte();
        
    } catch (error) {
        console.error('Error al generar reporte:', error);
        alert('❌ Error al generar el reporte. Intente nuevamente.');
        
        mensajeReporte.style.display = 'none';
        
        // Rehabilitar botón
        this.disabled = false;
        this.textContent = '📄 Generar Reporte';
        validarReporte();
    }
});