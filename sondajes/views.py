from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import msal
import requests
from .models import RecortesProyecto, RecortesSondajes, RecortesRegistros
from .sharepoint_utils import SharePointManager
from .yolo_processor import YOLOProcessor
import traceback
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import zipfile
import io
import os
from datetime import datetime
from weasyprint import HTML
import tempfile
from django.template.loader import render_to_string
import time
import gc  # AGREGAR ESTO


def limpiar_memoria():
    """Forzar limpieza de memoria"""
    gc.collect()
    print("🧹 Memoria liberada")


def page_index(request):
    """Página principal - requiere autenticación"""
    user = request.session.get('user')
    
    if not user:
        return redirect('login')
    
    proyectos = RecortesProyecto.objects.all().values('codigo', 'nombre', 'operacion', 'mina', 'jefe')
    
    context = {
        'user': user,
        'proyectos': list(proyectos)
    }
    return render(request, "index.html", context)


def get_sondajes(request, codigo_proyecto):
    """API para obtener sondajes por código de proyecto"""
    try:
        sondajes = RecortesSondajes.objects.filter(
            codigo=codigo_proyecto
        ).values('id_sondaje_proyecto', 'hole_id')
        
        return JsonResponse({
            'success': True,
            'sondajes': list(sondajes)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def get_registros(request, id_sondaje):
    """API para obtener registros por ID de sondaje"""
    try:
        registros = RecortesRegistros.objects.filter(
            id_sondaje_proyecto=id_sondaje
        ).values(
            'id',
            'from_field',
            'to',
            'file_name',
            'file_name_2',
            'file_clean',
            'file_clean_2',
            'procesado',
            'fecha_hora',
            'usuario'
        )
        
        registros_list = list(registros)
        
        for registro in registros_list:
            if registro.get('fecha_hora'):
                registro['fecha_hora'] = registro['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'success': True,
            'registros': registros_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def get_imagenes_procesadas(request, id_sondaje):
    """
    API para obtener las URLs de las imágenes procesadas de un sondaje
    """
    sp_manager = None
    try:
        # Obtener token
        token_data = request.session.get('token')
        access_token = token_data.get('access_token') if token_data else None
        refresh_token = token_data.get('refresh_token') if token_data else None
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No hay token de acceso'
            }, status=401)
        
        # Obtener registros procesados
        registros = RecortesRegistros.objects.filter(
            id_sondaje_proyecto=id_sondaje,
            procesado=True
        ).order_by('from_field')
        
        if not registros.exists():
            return JsonResponse({
                'success': False,
                'error': 'No hay registros procesados para este sondaje'
            })
        
        # Obtener información del sondaje
        sondaje = RecortesSondajes.objects.get(id_sondaje_proyecto=id_sondaje)
        codigo_proyecto = sondaje.codigo.codigo
        
        # Inicializar SharePoint Manager
        sp_manager = SharePointManager(
            access_token=access_token,
            refresh_token=refresh_token,
            session=request.session
        )
        
        # Construir la ruta base
        carpeta_caja = f"{settings.NAME_FOLDER}/Proyecto_{codigo_proyecto}/Caja_Sondaje_{id_sondaje}"
        
        imagenes_data = []
        
        for registro in registros:
            # Obtener nombres base de las imágenes originales
            img1_nombre = registro.file_name.replace('.png', '').replace('.jpg', '') if registro.file_name else None
            img2_nombre = registro.file_name_2.replace('.png', '').replace('.jpg', '') if registro.file_name_2 else None
            
            # Construir rutas de imágenes procesadas
            imagen1_path = f"{carpeta_caja}/{img1_nombre}.png" if img1_nombre else None
            imagen2_path = f"{carpeta_caja}/{img2_nombre}.png" if img2_nombre else None
            
            # Obtener URLs de descarga
            imagen1_url = sp_manager.get_image_url(imagen1_path) if imagen1_path else None
            imagen2_url = sp_manager.get_image_url(imagen2_path) if imagen2_path else None
            
            imagenes_data.append({
                'id': registro.id,
                'from': registro.from_field,
                'to': registro.to,
                'imagen1': {
                    'url': imagen1_url,
                    'path': imagen1_path,
                    'nombre': f"{img1_nombre}.png" if img1_nombre else None
                },
                'imagen2': {
                    'url': imagen2_url,
                    'path': imagen2_path,
                    'nombre': f"{img2_nombre}.png" if img2_nombre else None
                }
            })
        
        return JsonResponse({
            'success': True,
            'imagenes': imagenes_data
        })
        
    except RecortesSondajes.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Sondaje no encontrado'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en get_imagenes_procesadas: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    finally:
        # Liberar recursos
        if sp_manager:
            del sp_manager
        limpiar_memoria()


def descargar_imagenes_zip(request):
    """
    Descarga las imágenes seleccionadas en un archivo ZIP
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    sp_manager = None
    zip_buffer = None
    
    try:
        # Obtener token
        token_data = request.session.get('token')
        access_token = token_data.get('access_token') if token_data else None
        refresh_token = token_data.get('refresh_token') if token_data else None
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No hay token de acceso'
            }, status=401)
        
        # Obtener datos de la petición
        data = json.loads(request.body)
        imagenes_seleccionadas = data.get('imagenes', [])
        
        if not imagenes_seleccionadas:
            return JsonResponse({
                'success': False,
                'error': 'No hay imágenes seleccionadas'
            }, status=400)
        
        print(f"📦 Preparando ZIP con {len(imagenes_seleccionadas)} imágenes...")
        
        # Inicializar SharePoint Manager
        sp_manager = SharePointManager(
            access_token=access_token,
            refresh_token=refresh_token,
            session=request.session
        )
        
        # Crear ZIP en memoria
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, imagen_path in enumerate(imagenes_seleccionadas, 1):
                print(f"📥 Descargando imagen {idx}/{len(imagenes_seleccionadas)}: {imagen_path}")
                
                # Descargar imagen como bytes
                image_bytes = sp_manager.download_image_bytes(imagen_path)
                
                if image_bytes:
                    # Obtener solo el nombre del archivo
                    file_name = imagen_path.split('/')[-1]
                    
                    # Agregar al ZIP
                    zip_file.writestr(file_name, image_bytes)
                    print(f"✅ Agregada al ZIP: {file_name}")
                    
                    # Liberar bytes inmediatamente
                    del image_bytes
                else:
                    print(f"⚠️ No se pudo descargar: {imagen_path}")
                
                # Limpiar cada 10 imágenes
                if idx % 10 == 0:
                    limpiar_memoria()
        
        # Preparar respuesta
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.getvalue()
        
        response = HttpResponse(zip_bytes, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="imagenes_cajas.zip"'
        
        print(f"✅ ZIP generado exitosamente")
        
        return response
        
    except Exception as e:
        print(f"❌ Error en descargar_imagenes_zip: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    finally:
        # Liberar recursos
        if sp_manager:
            del sp_manager
        if zip_buffer:
            zip_buffer.close()
            del zip_buffer
        limpiar_memoria()


def login(request):
    """Inicia el flujo de autenticación con Microsoft"""
    msal_app = _build_msal_app()
    
    auth_url = msal_app.get_authorization_request_url(
        scopes=settings.SCOPE,
        redirect_uri=settings.REDIRECT_URI
    )
    
    return redirect(auth_url)


def azure_callback(request):
    """Callback que recibe el código de autorización de Microsoft"""
    code = request.GET.get('code')
    
    if not code:
        return HttpResponse('Error: No se recibió código de autorización', status=400)
    
    msal_app = _build_msal_app()
    
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=settings.SCOPE,
        redirect_uri=settings.REDIRECT_URI
    )
    
    if "error" in result:
        return HttpResponse(f'Error: {result.get("error_description")}', status=400)
    
    # GUARDAR TOKEN COMPLETO
    request.session['token'] = {
        'access_token': result.get('access_token'),
        'refresh_token': result.get('refresh_token'),
        'expires_in': result.get('expires_in', 3600),
        'timestamp': time.time()
    }
    
    user_info = _get_user_info(result['access_token'])
    request.session['user'] = user_info

    print("✅ Token guardado con refresh_token")
    
    return redirect('index')


def logout(request):
    """Cerrar sesión"""
    request.session.flush()

    logout_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri=https://10.211.0.185/login/"
    )

    return redirect(logout_url)


def _build_msal_app(cache=None):
    """Construye la aplicación MSAL"""
    return msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        client_credential=settings.AZURE_CLIENT_SECRET,
        authority=settings.AUTHORITY,
        token_cache=cache
    )


def _get_user_info(access_token):
    """Obtiene información del usuario desde Microsoft Graph"""
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(graph_endpoint, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

    
@ensure_csrf_cookie
def procesar_imagenes(request):
    """
    Procesa las imágenes de un registro con YOLO
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    sp_manager = None
    yolo_processor = None
    imagen = None
    imagen_caja = None
    imagen_caja_info = None
    
    try:
        data = json.loads(request.body)
        id_registro = data.get('id_registro')
        codigo_proyecto = data.get('codigo_proyecto')
        hole_id = data.get('hole_id')
        id_sondaje = data.get('id_sondaje')
        
        print("=" * 60)
        print(f"INICIANDO PROCESAMIENTO")
        print("Hora de inicio:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(f"ID Registro: {id_registro}")
        print(f"Código Proyecto: {codigo_proyecto}")
        print(f"Hole ID: {hole_id}")
        print(f"ID Sondaje: {id_sondaje}")
        print("=" * 60)
        
        registro = RecortesRegistros.objects.get(id=id_registro)
        
        if registro.procesado:
            return JsonResponse({
                'success': False,
                'error': 'Este registro ya fue procesado'
            })
        
        token_data = request.session.get('token')
        access_token = token_data.get('access_token') if token_data else None
        refresh_token = token_data.get('refresh_token') if token_data else None
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No hay token de acceso. Por favor, vuelve a iniciar sesión.'
            }, status=401)
        
        print(f"✅ Token obtenido")
        
        sp_manager = SharePointManager(
            access_token=access_token,
            refresh_token=refresh_token,
            session=request.session
        )
        yolo_processor = YOLOProcessor()
        
        base_path = f"{settings.SHAREPOINT_FOLDER_PATH}/{codigo_proyecto}/{hole_id}"
        print(f"Ruta base: {base_path}")
        
        resultados = []
        
        for idx, file_name in enumerate([registro.file_name, registro.file_name_2], 1):
            if not file_name:
                continue
            
            print(f"\n{'='*50}")
            print(f"IMAGEN {idx}: {file_name}")
            print(f"{'='*50}")
            
            imagen_path = f"{base_path}/{file_name}"
            imagen = sp_manager.get_image_from_sharepoint(imagen_path)
            
            if imagen is None:
                resultados.append({
                    'file': file_name,
                    'status': 'error',
                    'message': 'No se pudo descargar'
                })
                continue
            
            imagen_caja_info, imagen_caja = yolo_processor.process_image(imagen)
            
            carpeta_caja = f"{settings.NAME_FOLDER}/Proyecto_{codigo_proyecto}/Caja_Sondaje_{id_sondaje}"
            carpeta_info = f"{settings.NAME_FOLDER}/Proyecto_{codigo_proyecto}/Info_Caja_Sondaje_{id_sondaje}"
            
            nombre_base = file_name.replace('.png', '').replace('.jpg', '')
            upload_success = True
            
            if imagen_caja:
                if not sp_manager.upload_image_to_sharepoint(imagen_caja, carpeta_caja, f"{nombre_base}.png"):
                    upload_success = False
            
            if imagen_caja_info:
                if not sp_manager.upload_image_to_sharepoint(imagen_caja_info, carpeta_info, f"{nombre_base}.png"):
                    upload_success = False
            
            resultados.append({
                'file': file_name,
                'status': 'success' if upload_success else 'partial',
                'caja_detectada': imagen_caja is not None,
                'info_detectada': imagen_caja_info is not None
            })
            
            if idx == 1 and imagen_caja:
                registro.file_clean = f"{carpeta_caja}/{nombre_base}.png"
            elif idx == 2 and imagen_caja:
                registro.file_clean_2 = f"{carpeta_caja}/{nombre_base}.png"
            
            # Liberar imágenes procesadas
            if imagen:
                del imagen
                imagen = None
            if imagen_caja:
                del imagen_caja
                imagen_caja = None
            if imagen_caja_info:
                del imagen_caja_info
                imagen_caja_info = None
            
            # Limpiar memoria después de cada imagen
            limpiar_memoria()
        
        if any(r['status'] != 'error' for r in resultados):
            registro.procesado = True
            registro.save()
        
        print("Hora de finalización:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        return JsonResponse({
            'success': True,
            'message': 'Procesamiento completado',
            'resultados': resultados
        })
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR:")
        print(traceback.format_exc())
        print("=" * 60)
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    finally:
        # Liberar TODOS los recursos
        if imagen:
            del imagen
        if imagen_caja:
            del imagen_caja
        if imagen_caja_info:
            del imagen_caja_info
        if yolo_processor:
            del yolo_processor
        if sp_manager:
            del sp_manager
        
        limpiar_memoria()
    

@ensure_csrf_cookie
def generar_reporte(request):
    """
    Genera reporte PDF con las imágenes seleccionadas
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    sp_manager = None
    pdf_bytes = None
    docx_bytes = None
    zip_bytes = None
    
    try:
        import base64
        
        # Obtener datos del request
        logo = request.FILES.get('logo')
        tipo_informe = request.POST.get('tipo_informe')
        id_sondaje = request.POST.get('id_sondaje')
        imagenes_json = request.POST.get('imagenes')
        generar_docx = request.POST.get('generar_docx', 'false') == 'true'
        
        if not all([logo, tipo_informe, id_sondaje, imagenes_json]):
            return JsonResponse({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            }, status=400)
        
        imagenes_seleccionadas = json.loads(imagenes_json)
        
        print("=" * 60)
        print(f"📄 GENERANDO REPORTE {'PDF + DOCX' if generar_docx else 'PDF'}")
        print("Hora de inicio:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(f"Tipo: {tipo_informe}cm")
        print(f"ID Sondaje: {id_sondaje}")
        print(f"Imágenes: {len(imagenes_seleccionadas)}")
        print("=" * 60)
        
        # Obtener token
        token_data = request.session.get('token')
        access_token = token_data.get('access_token') if token_data else None
        refresh_token = token_data.get('refresh_token') if token_data else None
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No hay token de acceso'
            }, status=401)
        
        # Obtener información del sondaje y proyecto
        sondaje = RecortesSondajes.objects.get(id_sondaje_proyecto=id_sondaje)
        proyecto = sondaje.codigo
        
        # Convertir logo a Base64
        print("📷 Convirtiendo logo a Base64...")
        logo_bytes = logo.read()
        logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
        logo_data_uri = f"data:image/png;base64,{logo_base64}"
        
        # Liberar logo
        del logo_bytes
        
        # Inicializar SharePoint Manager
        sp_manager = SharePointManager(
            access_token=access_token,
            refresh_token=refresh_token,
            session=request.session
        )
        
        # Descargar y convertir imágenes a Base64
        print(f"📥 Procesando {len(imagenes_seleccionadas)} imágenes...")
        imagenes_info = []
        
        for idx, img_data in enumerate(imagenes_seleccionadas):
            if (idx + 1) % 10 == 0 or idx == 0:
                print(f"   Progreso: {idx + 1}/{len(imagenes_seleccionadas)}")
            
            image_bytes = sp_manager.download_image_bytes(img_data['path'])
            
            if image_bytes:
                img_base64 = base64.b64encode(image_bytes).decode('utf-8')
                img_data_uri = f"data:image/png;base64,{img_base64}"
                
                # Liberar inmediatamente
                del image_bytes
                del img_base64
                
                imagenes_info.append({
                    'data_uri': img_data_uri,
                    'Numero': img_data['numero'],
                    'Profundidad': f"{img_data['from']}m - {img_data['to']}m"
                })
            else:
                print(f"⚠️ No se pudo descargar imagen {idx + 1}")
            
            # Limpiar cada 10 imágenes
            if (idx + 1) % 10 == 0:
                limpiar_memoria()
        
        print(f"✅ {len(imagenes_info)} imágenes procesadas")
        
        # Agrupar imágenes según el tipo de informe
        if tipo_informe == '60':
            grupos_por_hoja = []
            for i in range(0, len(imagenes_info), 6):
                grupo = imagenes_info[i:i+6]
                pares = []
                for j in range(0, len(grupo), 2):
                    par = grupo[j:j+2]
                    while len(par) < 2:
                        par.append(None)
                    pares.append(par)
                grupos_por_hoja.append(pares)
        else:
            grupos_por_hoja = []
            for i in range(0, len(imagenes_info), 3):
                grupo = imagenes_info[i:i+3]
                grupos_por_hoja.append(grupo)
        
        # Preparar contexto
        context = {
            'Hole_Id': sondaje.hole_id,
            'Codigo': proyecto.codigo,
            'Nombre': proyecto.nombre,
            'Mina': proyecto.mina,
            'Total': len(imagenes_seleccionadas),
            'Fecha': datetime.now().strftime('%d/%m/%Y'),
            'grupos_por_hoja': grupos_por_hoja,
            'logo_data_uri': logo_data_uri
        }
        
        # Generar HTML y PDF
        template_name = f'plantilla{tipo_informe}.html'
        html_string = render_to_string(template_name, context)
        
        print("📄 Generando PDF con WeasyPrint...")
        pdf_buffer = io.BytesIO()
        HTML(string=html_string).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        # Liberar recursos intermedios
        del html_string
        del context
        del imagenes_info
        del grupos_por_hoja
        limpiar_memoria()
        
        print("✅ PDF generado exitosamente")
        
        # Si solo PDF, retornar directamente
        if not generar_docx:
            print("Hora de finalización:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print("=" * 60)
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{sondaje.hole_id}_{tipo_informe}cm.pdf"'
            return response
        
        # Si PDF + DOCX, convertir y crear ZIP
        print("📄 Convirtiendo PDF a DOCX...")
        
        try:
            # Convertir PDF a DOCX
            docx_bytes = convertir_pdf_a_docx(pdf_bytes)
            
            if not docx_bytes or len(docx_bytes) == 0:
                raise Exception("DOCX generado está vacío")
            
            print(f"✅ DOCX generado exitosamente ({len(docx_bytes)/1024/1024:.2f}MB)")
            
            # COMPRIMIR IMÁGENES DEL DOCX
            docx_bytes = comprimir_imagenes_docx(docx_bytes, quality=80)
            
            print(f"✅ DOCX optimizado ({len(docx_bytes)/1024/1024:.2f}MB)")
            
            # Crear ZIP
            print("📦 Creando ZIP...")
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                print(f"   Agregando PDF al ZIP ({len(pdf_bytes)/1024/1024:.2f}MB)...")
                zip_file.writestr(
                    f'reporte_{sondaje.hole_id}_{tipo_informe}cm.pdf',
                    pdf_bytes
                )
                
                print(f"   Agregando DOCX al ZIP ({len(docx_bytes)/1024/1024:.2f}MB)...")
                zip_file.writestr(
                    f'reporte_{sondaje.hole_id}_{tipo_informe}cm.docx',
                    docx_bytes
                )
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            zip_buffer.close()
            
            if not zip_bytes or len(zip_bytes) == 0:
                raise Exception("ZIP generado está vacío")
            
            print(f"✅ ZIP generado exitosamente ({len(zip_bytes)/1024/1024:.2f}MB)")
            print("Hora de finalización:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print("=" * 60)
            
            response = HttpResponse(zip_bytes, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="reporte_{sondaje.hole_id}_{tipo_informe}cm.zip"'
            return response
            
        except Exception as docx_error:
            print("=" * 60)
            print(f"❌ Error al generar DOCX: {docx_error}")
            print(traceback.format_exc())
            print("=" * 60)
            print("⚠️ Retornando solo PDF debido al error en DOCX...")
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{sondaje.hole_id}_{tipo_informe}cm.pdf"'
            return response
        
    except RecortesSondajes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sondaje no encontrado'}, status=404)
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR EN GENERAR_REPORTE:")
        print(traceback.format_exc())
        print("=" * 60)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        # Liberar TODOS los recursos
        if sp_manager:
            del sp_manager
        if pdf_bytes:
            del pdf_bytes
        if docx_bytes:
            del docx_bytes
        if zip_bytes:
            del zip_bytes
        
        limpiar_memoria()


def convertir_pdf_a_docx(pdf_bytes: bytes) -> bytes:
    """
    Convierte un PDF ya generado a DOCX usando pdf2docx
    """
    import gc
    
    timestamp = int(time.time() * 1000)
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"temp_pdf_{timestamp}.pdf")
    docx_path = os.path.join(temp_dir, f"temp_docx_{timestamp}.docx")
    
    converter = None
    docx_bytes = None
    
    try:
        print(f"   Guardando PDF temporal: {pdf_path}")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        from pdf2docx import Converter
        
        print(f"   Convirtiendo PDF a DOCX...")
        converter = Converter(pdf_path)
        converter.convert(docx_path, start=0, end=None)
        converter.close()
        converter = None
        
        time.sleep(0.3)
        
        print(f"   Leyendo DOCX generado: {docx_path}")
        with open(docx_path, 'rb') as f:
            docx_bytes = f.read()
        
        print(f"   ✅ DOCX generado correctamente ({len(docx_bytes)} bytes)")
        return docx_bytes
        
    except ImportError:
        raise Exception("pdf2docx no está instalado. Instala con: pip install pdf2docx")
    except Exception as e:
        print(f"   ❌ Error en conversión: {e}")
        raise
    finally:
        if converter is not None:
            try:
                converter.close()
            except:
                pass
        
        gc.collect()
        time.sleep(0.3)
        
        for file_path in [pdf_path, docx_path]:
            if os.path.exists(file_path):
                for intento in range(3):
                    try:
                        os.remove(file_path)
                        print(f"   🧹 Eliminado: {file_path}")
                        break
                    except PermissionError:
                        if intento < 2:
                            time.sleep(0.2)
                        else:
                            print(f"   ⚠️ No se pudo eliminar: {file_path}")
                    except Exception as e:
                        print(f"   ⚠️ Error al eliminar {file_path}: {e}")
                        break


def comprimir_imagenes_docx(docx_bytes: bytes, quality: int = 80) -> bytes:
    """
    Comprime las imágenes dentro de un DOCX para reducir su tamaño
    """
    from docx import Document
    from PIL import Image
    import io
    
    print(f"   🗜️ Comprimiendo imágenes del DOCX (calidad={quality})...")
    
    size_original_mb = len(docx_bytes) / (1024 * 1024)
    print(f"   📦 Tamaño original: {size_original_mb:.2f}MB")
    
    try:
        docx_buffer = io.BytesIO(docx_bytes)
        doc = Document(docx_buffer)
        
        rels = doc.part.rels
        imagenes_comprimidas = 0
        
        for rel in rels:
            if "image" in rels[rel].target_ref:
                image_part = rels[rel]._target
                image_data = image_part.blob
                
                try:
                    image = Image.open(io.BytesIO(image_data))
                    size_antes = len(image_data)
                    
                    if image.mode in ("RGBA", "LA", "P"):
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "P":
                            image = image.convert("RGBA")
                        background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
                        image = background
                    
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=quality, optimize=True)
                    
                    image_part._blob = buffer.getvalue()
                    
                    size_despues = len(buffer.getvalue())
                    reduccion = ((size_antes - size_despues) / size_antes) * 100
                    
                    imagenes_comprimidas += 1
                    
                    if imagenes_comprimidas <= 3:
                        print(f"      Imagen {imagenes_comprimidas}: {size_antes/1024:.1f}KB → {size_despues/1024:.1f}KB (-{reduccion:.1f}%)")
                    
                    # Liberar recursos de imagen
                    del image
                    buffer.close()
                    del buffer
                    del image_data
                    
                except Exception as e:
                    print(f"   ⚠️ No se pudo comprimir una imagen: {e}")
        
        print(f"   ✅ {imagenes_comprimidas} imágenes comprimidas")
        
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        output_buffer.seek(0)
        docx_comprimido = output_buffer.getvalue()
        output_buffer.close()
        
        # Liberar documentos
        del doc
        docx_buffer.close()
        del docx_buffer
        
        size_final_mb = len(docx_comprimido) / (1024 * 1024)
        reduccion_total = ((size_original_mb - size_final_mb) / size_original_mb) * 100
        
        print(f"   📦 Tamaño final: {size_final_mb:.2f}MB")
        print(f"   ✅ Reducción total: {reduccion_total:.1f}%")
        
        return docx_comprimido
        
    except Exception as e:
        print(f"   ❌ Error al comprimir DOCX: {e}")
        print(f"   ⚠️ Retornando DOCX sin comprimir")
        return docx_bytes