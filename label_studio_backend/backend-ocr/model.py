import os
import uuid
import easyocr
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_image_local_path
from PIL import Image

print("Inicializando EasyOCR...", flush=True)
# gpu=True se tiver GPU, senão False
try:
    READER = easyocr.Reader(['pt'], gpu=False) 
    print("EasyOCR pronto.", flush=True)
except:
    print("Erro ao carregar EasyOCR. Verifique instalação.", flush=True)

class EasyOCRModel(LabelStudioMLBase):
    
    def predict(self, tasks, **kwargs):
        predictions = []

        for task in tasks:
            try:
                # 1. Carrega Imagem
                image_url = task['data']['image']
                image_path = get_image_local_path(image_url)
                
                if not os.path.exists(image_path): continue

                with Image.open(image_path) as img:
                    img_width, img_height = img.size

                print(f"Processando OCR: {image_url}")
                
                # 2. Roda EasyOCR
                results = READER.readtext(image_path, detail=1)
                result_items = []
                
                for (bbox, text, confidence) in results:
                    if not text.strip(): continue # Ignora vazio

                    # --- GEOMETRIA ---
                    x_min = min([pt[0] for pt in bbox])
                    y_min = min([pt[1] for pt in bbox])
                    x_max = max([pt[0] for pt in bbox])
                    y_max = max([pt[1] for pt in bbox])
                    
                    # Converte para % do Label Studio
                    x = (x_min / img_width) * 100
                    y = (y_min / img_height) * 100
                    w = ((x_max - x_min) / img_width) * 100
                    h = ((y_max - y_min) / img_height) * 100

                    # --- CRIAÇÃO DO OBJETO ---
                    region_id = str(uuid.uuid4())[:10]

                    # Apenas TRANSCRICÃO (Texto), sem rótulo (Label)
                    # Isso cria a caixa clicável com o texto dentro
                    result_items.append({
                        "id": region_id,
                        "from_name": "transcription", 
                        "to_name": "image", 
                        "type": "textarea",
                        "value": {
                            "x": x, "y": y, "width": w, "height": h,
                            "rotation": 0, "text": [text]
                        }
                    })


                predictions.append({"result": result_items})
            
            except Exception as e:
                print(f"Erro no OCR: {e}", flush=True)

        return predictions