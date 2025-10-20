from django.conf import settings
import io
from PIL import Image
import requests
import urllib.parse
import msal
import time
import gc  # AGREGAR


class SharePointManager:
    def __init__(self, access_token=None, refresh_token=None, session=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.session = session
        self.site_url = settings.SHAREPOINT_SITE_URL
        
        parts = self.site_url.replace('https://', '').split('/')
        self.hostname = parts[0]
        self.site_path = '/'.join(parts[1:]) if len(parts) > 1 else ''
        
        self._site_id = None
        self._drive_id = None
    
    def renovar_token(self):
        """Renueva el access token usando el refresh token"""
        if not self.refresh_token:
            print("❌ No hay refresh_token disponible para renovar")
            return False
        
        try:
            print("🔄 Token expirado, renovando...")
            
            app = msal.ConfidentialClientApplication(
                settings.AZURE_CLIENT_ID,
                authority=settings.AUTHORITY,
                client_credential=settings.AZURE_CLIENT_SECRET
            )
            
            result = app.acquire_token_by_refresh_token(
                self.refresh_token,
                scopes=settings.SCOPE
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                
                if "refresh_token" in result:
                    self.refresh_token = result["refresh_token"]
                
                if self.session:
                    self.session['token'] = {
                        'access_token': result['access_token'],
                        'refresh_token': result.get('refresh_token', self.refresh_token),
                        'expires_in': result.get('expires_in', 3600),
                        'timestamp': time.time()
                    }
                    self.session.modified = True
                
                print("✅ Token renovado exitosamente")
                return True
            else:
                error_desc = result.get('error_description', result.get('error', 'Error desconocido'))
                print(f"❌ Error renovando token: {error_desc}")
                return False
                
        except Exception as e:
            print(f"❌ Excepción al renovar token: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def _hacer_peticion_con_reintentos(self, method, url, max_reintentos=2, **kwargs):
        """Hace una petición HTTP con renovación automática de token"""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        for intento in range(max_reintentos):
            response = requests.request(method, url, **kwargs)
            
            if response.status_code != 401:
                return response
            
            print(f"⚠️ Error 401: Token expirado (intento {intento + 1}/{max_reintentos})")
            
            if self.refresh_token and intento < max_reintentos - 1:
                if self.renovar_token():
                    kwargs['headers']['Authorization'] = f'Bearer {self.access_token}'
                    print("🔄 Reintentando petición con token renovado...")
                    continue
                else:
                    print("❌ No se pudo renovar el token")
                    break
            else:
                print("❌ No hay refresh_token o se agotaron los reintentos")
                break
        
        return response
    
    def get_site_id(self):
        """Obtiene el ID del sitio de SharePoint"""
        if self._site_id:
            return self._site_id
            
        try:
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{self.hostname}:/{self.site_path}"
            response = self._hacer_peticion_con_reintentos('GET', graph_url)
            
            if response.status_code == 200:
                site_data = response.json()
                self._site_id = site_data.get('id')
                print(f"✅ Site ID obtenido: {self._site_id}")
                return self._site_id
            else:
                print(f"❌ Error obteniendo Site ID: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Excepción obteniendo Site ID: {str(e)}")
            return None
    
    def get_drive_id(self, site_id, drive_name="Teams Wiki Data"):
        """Obtiene el ID del drive"""
        if self._drive_id:
            return self._drive_id
            
        try:
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            response = self._hacer_peticion_con_reintentos('GET', graph_url)
            
            if response.status_code == 200:
                drives = response.json().get('value', [])
                
                for drive in drives:
                    if drive.get('name') == drive_name:
                        self._drive_id = drive.get('id')
                        print(f"✅ Drive ID obtenido para '{drive_name}': {self._drive_id}")
                        return self._drive_id
                
                if drives:
                    self._drive_id = drives[0].get('id')
                    print(f"⚠️ Drive '{drive_name}' no encontrado, usando primer drive: {self._drive_id}")
                    return self._drive_id
                else:
                    print(f"❌ No se encontraron drives en el sitio")
                    return None
            else:
                print(f"❌ Error obteniendo drives: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Excepción obteniendo Drive ID: {str(e)}")
            return None
    
    def get_image_from_sharepoint(self, file_path):
        """Descarga una imagen desde SharePoint"""
        image_stream = None
        try:
            if not self.access_token:
                print("❌ No hay token de acceso disponible")
                return None
            
            site_id = self.get_site_id()
            if not site_id:
                return None
            
            drive_id = self.get_drive_id(site_id, "Teams Wiki Data")
            if not drive_id:
                return None
            
            encoded_path = urllib.parse.quote(file_path)
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
            
            print(f"Descargando: {file_path}")
            
            response = self._hacer_peticion_con_reintentos('GET', graph_url)
            
            if response.status_code == 200:
                image_stream = io.BytesIO(response.content)
                image = Image.open(image_stream)
                print(f"✅ Imagen descargada: {image.size}")
                
                # Crear copia para que no dependa del stream
                image_copy = image.copy()
                
                # Liberar recursos
                image.close()
                image_stream.close()
                del response
                del image
                
                return image_copy
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error al descargar imagen {file_path}: {str(e)}")
            return None
        finally:
            if image_stream:
                image_stream.close()
            gc.collect()
    
    def get_image_url(self, file_path):
        """Obtiene la URL de descarga temporal de una imagen"""
        try:
            if not self.access_token:
                return None
            
            site_id = self.get_site_id()
            if not site_id:
                return None
            
            drive_id = self.get_drive_id(site_id, "Teams Wiki Data")
            if not drive_id:
                return None
            
            encoded_path = urllib.parse.quote(file_path)
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"
            
            response = self._hacer_peticion_con_reintentos('GET', graph_url)
            
            if response.status_code == 200:
                file_data = response.json()
                download_url = file_data.get('@microsoft.graph.downloadUrl')
                
                # Liberar response
                del response
                del file_data
                
                return download_url
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error obteniendo URL: {str(e)}")
            return None
    
    def download_image_bytes(self, file_path):
        """Descarga una imagen como bytes"""
        try:
            if not self.access_token:
                return None
            
            site_id = self.get_site_id()
            if not site_id:
                return None
            
            drive_id = self.get_drive_id(site_id, "Teams Wiki Data")
            if not drive_id:
                return None
            
            encoded_path = urllib.parse.quote(file_path)
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
            
            response = self._hacer_peticion_con_reintentos('GET', graph_url)
            
            if response.status_code == 200:
                content = response.content
                
                # Liberar response
                del response
                
                return content
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error descargando bytes: {str(e)}")
            return None
        finally:
            gc.collect()
    
    def upload_image_to_sharepoint(self, image, folder_path, file_name):
        """Sube una imagen a SharePoint"""
        img_byte_arr = None
        try:
            if not self.access_token:
                print("❌ No hay token de acceso disponible")
                return False
            
            site_id = self.get_site_id()
            if not site_id:
                return False
            
            drive_id = self.get_drive_id(site_id, "Teams Wiki Data")
            if not drive_id:
                return False
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=80, optimize=True)
            img_byte_arr.seek(0)
            content = img_byte_arr.getvalue()
            
            full_path = f"{folder_path}/{file_name}"
            encoded_path = urllib.parse.quote(full_path)
            
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
            
            print(f"Subiendo: {file_name}")
            
            response = self._hacer_peticion_con_reintentos(
                'PUT', 
                graph_url, 
                headers={'Content-Type': 'image/png'},
                data=content
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Imagen subida: {file_name}")
                
                # Liberar recursos
                del content
                del response
                
                return True
            else:
                print(f"❌ Error HTTP {response.status_code}")
                
                if response.status_code == 404:
                    print("Creando carpetas...")
                    if self._ensure_folder_exists(site_id, drive_id, folder_path):
                        response = self._hacer_peticion_con_reintentos(
                            'PUT',
                            graph_url,
                            headers={'Content-Type': 'image/png'},
                            data=content
                        )
                        if response.status_code in [200, 201]:
                            print(f"✅ Imagen subida (segundo intento)")
                            return True
                
                return False
                
        except Exception as e:
            print(f"❌ Error al subir: {str(e)}")
            return False
        finally:
            if img_byte_arr:
                img_byte_arr.close()
                del img_byte_arr
            gc.collect()
    
    def _ensure_folder_exists(self, site_id, drive_id, folder_path):
        """Crea la estructura de carpetas si no existe"""
        try:
            parts = [p for p in folder_path.split('/') if p]
            current_path = ""
            
            for folder in parts:
                parent_path = current_path
                current_path = f"{current_path}/{folder}" if current_path else folder
                
                if parent_path:
                    encoded_parent = urllib.parse.quote(parent_path)
                    graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_parent}:/children"
                else:
                    graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
                
                body = {
                    "name": folder,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "replace"
                }
                
                response = self._hacer_peticion_con_reintentos(
                    'POST',
                    graph_url,
                    headers={'Content-Type': 'application/json'},
                    json=body
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Carpeta creada: {current_path}")
                elif response.status_code == 409:
                    print(f"✅ Carpeta existe: {current_path}")
                
                # Liberar response
                del response
            
            return True
            
        except Exception as e:
            print(f"❌ Error creando carpetas: {str(e)}")
            return False
    
    def __del__(self):
        """Limpiar al destruir el objeto"""
        if hasattr(self, '_site_id'):
            del self._site_id
        if hasattr(self, '_drive_id'):
            del self._drive_id
        gc.collect()