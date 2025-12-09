import json
import re
from pathlib import Path
from PIL import Image
from datasets import Dataset, Features, Sequence, ClassLabel, Value, Array2D, Array3D
from transformers import AutoProcessor
import warnings
warnings.filterwarnings("ignore")

JSON_FILE = "annotations.json" 
IMAGE_FOLDER = "nfes/" 
MODEL_ID = "microsoft/layoutlmv3-base"

LABELS_LIST = [
    "O", 
    "CHAVE_ACESSO",
    "NOME_EMITENTE",
    "CNPJ_EMITENTE",
    "NOME_DESTINATARIO",
    "CNPJ_DESTINATARIO",
    "DATA_EMISSAO",
    "VALOR_TOTAL",
    "NUM_NOTA_FISCAL",
    "NUM_SERIE"
]

def clean_text_content(label, text):
    text = text.strip()
    if label == "NUM_NOTA_FISCAL":
        return re.sub(r'(?i)^(n[º°oª\.]|num\.|nota\s*fiscal)\s*', '', text).strip()
    if label == "NUM_SERIE":
        return re.sub(r'(?i)^(s[ée]rie|ser\.)\s*', '', text).strip()
    return text

def normalize_box(box, width, height):
    x, y, w, h = box
    x1 = int(x * 10)
    y1 = int(y * 10)
    x2 = int((x + w) * 10)
    y2 = int((y + h) * 10)
    return [max(0, min(1000, val)) for val in [x1, y1, x2, y2]]

def load_and_fix_data():
    import urllib.parse 

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_data = []

    for item in data:
        image_path = item['data']['image'] 
        raw_filename = Path(image_path).name.split('?')[0] 
        
        candidates = []
        candidates.append(raw_filename)
        if '-' in raw_filename:
            candidates.append(raw_filename.split('-', 1)[1])
        candidates.append(urllib.parse.unquote(raw_filename))

        full_image_path = None
        for candidate in candidates:
            p = Path(IMAGE_FOLDER) / candidate
            if p.exists():
                full_image_path = p
                break 
        
        if not full_image_path:
            print(f"Erro: Imagem nao encontrada: {candidates}")
            continue

        id_to_text = {}
        id_to_label = {}
        id_to_box = {}

        for annotation in item['annotations'][0]['result']:
            item_id = annotation['id']
            if annotation['type'] == 'textarea':
                id_to_text[item_id] = annotation['value']['text'][0]
            elif annotation['type'] == 'rectanglelabels':
                id_to_label[item_id] = annotation['value']['rectanglelabels'][0]
                val = annotation['value']
                id_to_box[item_id] = [val['x'], val['y'], val['width'], val['height']]

        words = []
        boxes = []
        ner_tags = [] 

        try:
            image = Image.open(full_image_path).convert("RGB")
        except Exception as e:
            print(f"Erro ao abrir imagem {full_image_path}: {e}")
            continue

        w, h = image.size

        for item_id, label in id_to_label.items():
            if item_id in id_to_text:
                if label == "Text": label = "O"
                if label not in LABELS_LIST: label = "O"

                raw_text = id_to_text[item_id]
                clean_text = clean_text_content(label, raw_text)
                
                if not clean_text: continue

                words.append(clean_text)
                boxes.append(normalize_box(id_to_box[item_id], w, h))
                ner_tags.append(label)

        processed_data.append({
            "image": image, 
            "tokens": words,
            "bboxes": boxes,
            "ner_tags": ner_tags 
        })

    return processed_data

raw_data = load_and_fix_data()

label2id = {label: i for i, label in enumerate(LABELS_LIST)}
id2label = {i: label for i, label in enumerate(LABELS_LIST)}

formatted_data = []
for entry in raw_data:
    formatted_data.append({
        "image": entry['image'],
        "tokens": entry['tokens'],
        "bboxes": entry['bboxes'],
        "ner_tags": [label2id[label] for label in entry['ner_tags']]
    })

ds = Dataset.from_list(formatted_data)

processor = AutoProcessor.from_pretrained(MODEL_ID, apply_ocr=False)

def prepare_dataset(examples):
    images = examples["image"]
    words = examples["tokens"]
    boxes = examples["bboxes"]
    word_labels = examples["ner_tags"]

    encoding = processor(
        images,
        words,
        boxes=boxes,
        word_labels=word_labels,
        truncation=True,
        padding="max_length",
        max_length=512
    )
    return encoding

features = Features({
    'pixel_values': Array3D(dtype="float32", shape=(3, 224, 224)),
    'input_ids': Sequence(feature=Value(dtype='int64')),
    'attention_mask': Sequence(feature=Value(dtype='int64')),
    'bbox': Array2D(dtype="int64", shape=(512, 4)),
    'labels': Sequence(feature=Value(dtype='int64')),
})

train_dataset = ds.map(
    prepare_dataset,
    batched=True,
    remove_columns=ds.column_names,
    features=features
)

print("Dataset pronto para treinamento")
print(train_dataset)

train_dataset.save_to_disk("processed_dataset")
print("Salvo em processed_dataset")