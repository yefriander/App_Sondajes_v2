import msal
from django.conf import settings

def get_sharepoint_token(user_token=None):
    """
    Obtiene un token específico para SharePoint usando el token del usuario
    """
    try:
        # Crear cliente MSAL
        app = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=settings.AUTHORITY
        )
        
        # Obtener token para SharePoint en nombre del usuario (on-behalf-of flow)
        if user_token:
            # Scope específico para SharePoint
            sharepoint_scope = [f"{settings.SHAREPOINT_SITE_URL}/.default"]
            
            result = app.acquire_token_on_behalf_of(
                user_assertion=user_token,
                scopes=sharepoint_scope
            )
            
            if "access_token" in result:
                print("✅ Token de SharePoint obtenido exitosamente")
                return result["access_token"]
            else:
                print(f"❌ Error obteniendo token de SharePoint: {result.get('error_description')}")
                return None
        
        # Si no hay token de usuario, usar client credentials
        sharepoint_scope = [f"{settings.SHAREPOINT_SITE_URL}/.default"]
        result = app.acquire_token_for_client(scopes=sharepoint_scope)
        
        if "access_token" in result:
            print("✅ Token de SharePoint (app-only) obtenido exitosamente")
            return result["access_token"]
        else:
            print(f"❌ Error obteniendo token de SharePoint: {result.get('error_description')}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción al obtener token de SharePoint: {str(e)}")
        return None