from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import os
from django.conf import settings
import gc


class YOLOProcessor:
    def __init__(self):
        model_path = os.path.join(settings.BASE_DIR, 'model', 'best.pt')
        self.model = YOLO(model_path)
        
        # Configurar para usar menos memoria
        self.model.overrides['verbose'] = False
        
        self.class_names = {0: 'caja', 1: 'caja_con_info'}
    
    def process_image(self, image):
        """
        Procesa una imagen con YOLO y libera memoria después
        """
        img_array = None
        results = None
        
        try:
            # Convertir PIL Image a formato compatible
            img_array = np.array(image)
            if img_array.shape[-1] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
             
            # Ejecutar detección
            results = self.model(img_array, verbose=False)
            
            imagen_caja = None
            imagen_caja_info = None
            
            # Procesar resultados
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if conf < 0.5:
                        continue
                    
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cropped = img_array[y1:y2, x1:x2]
                    cropped_pil = Image.fromarray(cropped)
                    
                    if cls == 0:  # caja
                        imagen_caja_info = cropped_pil
                    elif cls == 1:  # caja_con_info
                        imagen_caja = cropped_pil
                    
                    # Liberar cropped inmediatamente
                    del cropped
            
            return imagen_caja_info, imagen_caja
            
        finally:
            # Limpiar recursos
            if img_array is not None:
                del img_array
            if results is not None:
                del results
            gc.collect()
    
    def process_image_with_annotations(self, image):
        """Procesa una imagen y devuelve con anotaciones"""
        img_array = None
        results = None
        annotated_img = None
        
        try:
            img_array = np.array(image)
            if img_array.shape[-1] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            results = self.model(img_array, verbose=False)
            
            annotated_img = results[0].plot()
            annotated_img = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
            
            annotated_pil = Image.fromarray(annotated_img)
            
            return annotated_pil
            
        finally:
            if img_array is not None:
                del img_array
            if results is not None:
                del results
            if annotated_img is not None:
                del annotated_img
            gc.collect()
    
    def __del__(self):
        """Limpiar modelo al destruir"""
        if hasattr(self, 'model'):
            del self.model
        gc.collect()