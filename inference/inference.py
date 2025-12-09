import torch
import easyocr
import re
import os
import fitz  # PyMuPDF
import json
import uuid
from PIL import Image
from transformers import AutoModelForTokenClassification, AutoProcessor
import utils  
import warnings
warnings.filterwarnings("ignore")

INPUT_FOLDER = "documentos_entrada"
ACCEPTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.pdf')
MODEL_PATH = "layoutlmv3-finetuned-nfe"
CONFIDENCE_THRESHOLD = 0.50

LABELS_LIST = [
    "O", "CHAVE_ACESSO", "NOME_EMITENTE", "CNPJ_EMITENTE",
    "NOME_DESTINATARIO", "CNPJ_DESTINATARIO", "DATA_EMISSAO",
    "VALOR_TOTAL", "NUM_NOTA_FISCAL", "NUM_SERIE"
]
id2label = {i: label for i, label in enumerate(LABELS_LIST)}

class NFeProcessor:
    def __init__(self):
        print("Inicializando análise...", flush=True)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.reader = easyocr.Reader(['pt'], gpu=(self.device.type == 'cuda'), verbose=False)
        self.processor = AutoProcessor.from_pretrained(MODEL_PATH, apply_ocr=False)
        self.model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)
        self.model.to(self.device)

    def _convert_pdf_to_image(self, file_path):
        try:
            doc = fitz.open(file_path)
            page = doc.load_page(0)
            matrix = fitz.Matrix(3, 3)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            temp_name = f"temp_{uuid.uuid4()}.png"
            pix.save(temp_name)
            doc.close()
            return temp_name, True
        except Exception as e:
            raise Exception(f"PDF Conversion Failed: {str(e)}")

    def _retrieve_highest_value(self, ocr_results):
        candidates = []
        for bbox, text, prob in ocr_results:
            clean = text.replace("R$", "").strip()
            if re.search(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', clean):
                try:
                    v_float = float(clean.replace('.', '').replace(',', '.'))
                    if v_float > 0.01 and not (2020 <= v_float <= 2035): 
                        candidates.append((clean, v_float))
                except: continue
                
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        return None

    def process_file(self, file_path):
        temp_created = False
        processing_path = file_path

        try:
            if file_path.lower().endswith('.pdf'):
                processing_path, temp_created = self._convert_pdf_to_image(file_path)

            image = Image.open(processing_path).convert("RGB")
            width, height = image.size
            
            results = self.reader.readtext(processing_path) 

            words, boxes = [], []
            header_text = "" 

            for (bbox, text, prob) in results:
                y_med = (bbox[0][1] + bbox[2][1]) / 2
                if y_med < (height * 0.30): header_text += " " + text
                
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
                
                norm_box = [
                    int((x1 / width) * 1000), int((y1 / height) * 1000),
                    int((x2 / width) * 1000), int((y2 / height) * 1000)
                ]
                norm_box = [max(0, min(1000, val)) for val in norm_box]
                words.append(text); boxes.append(norm_box)

            encoding = self.processor(image, words, boxes=boxes, return_tensors="pt", truncation=True)
            for k,v in encoding.items(): encoding[k] = v.to(self.device)
            
            with torch.no_grad(): 
                outputs = self.model(**encoding)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            scores, predictions = torch.max(probs, dim=-1)
            scores = scores.squeeze().tolist()
            preds = predictions.squeeze().tolist()
            tokens = self.processor.tokenizer.convert_ids_to_tokens(encoding.input_ids.squeeze().tolist())
            token_boxes = encoding.bbox.squeeze().tolist()

            reconstructed_words = []
            current_word_obj = None

            if not isinstance(scores, list): 
                scores, preds, tokens, token_boxes = [scores], [preds], [tokens], [token_boxes]

            for p, s, t, b in zip(preds, scores, tokens, token_boxes):
                if t in ["<s>", "</s>", "<pad>"]: continue
                
                is_start_of_word = t.startswith("Ġ") or t.startswith(" ")
                clean_text = t.replace("Ġ", "").strip()
                if not clean_text: continue 

                if is_start_of_word or current_word_obj is None:
                    if current_word_obj: reconstructed_words.append(current_word_obj)
                    current_word_obj = {
                        "text": clean_text,
                        "label_id": p,
                        "label_name": id2label[p],
                        "score": s,
                        "x_pos": b[0],
                        "x_end": b[2], 
                        "box": b 
                    }
                else:
                    current_word_obj["text"] += clean_text
                    current_word_obj["x_end"] = b[2] 

            if current_word_obj: reconstructed_words.append(current_word_obj)

            confident_keys = [w for w in reconstructed_words if w["label_name"] == "CHAVE_ACESSO" and w["score"] > 0.4]
            
            if confident_keys:

                cluster_y1 = min([w["box"][1] for w in confident_keys])
                cluster_y2 = max([w["box"][3] for w in confident_keys])

                avg_y_center = (sum([w["box"][1] for w in confident_keys]) + sum([w["box"][3] for w in confident_keys])) / (2 * len(confident_keys))

                cluster_x_min = min([w["box"][0] for w in confident_keys])
                cluster_x_max = max([w["box"][2] for w in confident_keys])

                Y_TOLERANCE = 15
                X_GAP_LIMIT = 150

                for w in reconstructed_words:
                    if w["label_name"] != "CHAVE_ACESSO":
                        if not (re.fullmatch(r'\d{4}', w["text"]) or (w["text"].isdigit() and len(w["text"]) >= 2)):
                            continue

                        w_y_center = (w["box"][1] + w["box"][3]) / 2
                        if abs(w_y_center - avg_y_center) > Y_TOLERANCE:
                            continue

                        dist_to_left = abs(w["box"][2] - cluster_x_min) 
                        dist_to_right = abs(w["box"][0] - cluster_x_max) 
                        

                        if dist_to_left < X_GAP_LIMIT or dist_to_right < X_GAP_LIMIT:
                            w["label_name"] = "CHAVE_ACESSO"
                            w["score"] = 0.95 
                            
                            cluster_x_min = min(cluster_x_min, w["box"][0])
                            cluster_x_max = max(cluster_x_max, w["box"][2])

            final_data = {}
            
            for word in reconstructed_words:
                label_name = word["label_name"]
                score = word["score"]

                limit = 0.20 if label_name in ["NOME_DESTINATARIO", "VALOR_TOTAL", "CHAVE_ACESSO", "CNPJ_EMITENTE", "CNPJ_DESTINATARIO"] else CONFIDENCE_THRESHOLD
                
                if label_name == "O" or score < limit: continue
                
                if label_name not in final_data: final_data[label_name] = []
                final_data[label_name].append((word["text"], word["x_pos"]))

            match_invoice = re.search(r'(\d{3}\.\d{3}\.\d{3})', header_text)
            if match_invoice: final_data["NUM_NOTA_FISCAL"] = [(match_invoice.group(1), 0)]
            match_series = re.search(r'(?i)S[ÉE]RIE[:\s]*(\d+)', header_text)
            if match_series: final_data["NUM_SERIE"] = [(match_series.group(1), 0)]

            processed_data = {}
            for label, parts in final_data.items():
                parts.sort(key=lambda x: x[1])
                
                text = " ".join([p[0] for p in parts]).strip()
                
                if label == "CHAVE_ACESSO":
                    clean = re.sub(r'\D', '', text)
                    if len(clean) > 44: clean = clean[:44]
                    text = ' '.join([clean[i:i+4] for i in range(0, len(clean), 4)])
                
                final_text = utils.clean_field(label, text)
                if len(final_text) > 1:
                    processed_data[label] = final_text

            value_in_output = processed_data.get("VALOR_TOTAL", "")
            if not value_in_output:
                recovered_value = self._retrieve_highest_value(results)
                if recovered_value: processed_data["VALOR_TOTAL"] = recovered_value
            
            return processed_data

        except Exception as e:
            return {"erro": str(e)}
        finally:
            if temp_created and os.path.exists(processing_path):
                try: os.remove(processing_path)
                except: pass

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(json.dumps({"aviso": f"Folder '{INPUT_FOLDER}' created. Add files there."}))
    else:
        try:
            nfe_engine = NFeProcessor()
            
            files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(ACCEPTED_EXTENSIONS)]
            results_list = []
            
            if not files:
                print(json.dumps({"aviso": "No files found in input folder."}))
            else:
                for filename in files:
                    file_path = os.path.join(INPUT_FOLDER, filename)
                    
                    raw_result = nfe_engine.process_file(file_path)
                    
                    formatted_result = utils.format_output(filename, raw_result)
                    
                    results_list.append(formatted_result)

                print(json.dumps(results_list, indent=4, ensure_ascii=False))
                
        except Exception as e:
            print(json.dumps({"erro_fatal": str(e)}))