"""
URL configuration for testigos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from sondajes import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.page_index, name="index"),
    path('login/', views.login, name='login'),
    path('azure/callback/', views.azure_callback, name='azure_callback'),
    path('logout/', views.logout, name='logout'),

    # APIs para filtros
    path('api/sondajes/<str:codigo_proyecto>/', views.get_sondajes, name='get_sondajes'),
    path('api/registros/<int:id_sondaje>/', views.get_registros, name='get_registros'),

    # API para procesar imágenes
    path('api/procesar-imagenes/', views.procesar_imagenes, name='procesar_imagenes'),

    # APIs para visualizar y descargar imágenes
    path('api/imagenes-procesadas/<int:id_sondaje>/', views.get_imagenes_procesadas, name='get_imagenes_procesadas'),
    path('api/descargar-zip/', views.descargar_imagenes_zip, name='descargar_zip'),

    # NUEVA API para generar reportes
    path('api/generar-reporte/', views.generar_reporte, name='generar_reporte'),
]
