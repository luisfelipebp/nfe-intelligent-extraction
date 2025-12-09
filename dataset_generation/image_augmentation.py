import cv2
import os
import numpy as np
import albumentations as A

INPUT_DIR = "./generated_images/"
OUTPUT_DIR = "./dataset_images/"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

transform = A.Compose([
    A.ShiftScaleRotate(
        shift_limit=0.10,
        scale_limit=0.10,
        rotate_limit=3,
        border_mode=cv2.BORDER_CONSTANT, 
        value=(255, 255, 255),
        p=0.8
    ),
    A.OneOf([
        A.GaussianBlur(blur_limit=(3, 5), p=1),
        A.GaussNoise(var_limit=(10.0, 50.0), p=1),
        A.ImageCompression(quality_lower=50, quality_upper=80, p=1),
], p=0.3),
    A.RandomBrightnessContrast(p=0.3),
])

arquivos = [f for f in os.listdir(INPUT_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]

for arq in arquivos:
    caminho_img = os.path.join(INPUT_DIR, arq)
    image = cv2.imread(caminho_img)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    augmented = transform(image=image)["image"]
    augmented = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)
    
    nome_saida = f"aug_{arq}"
    cv2.imwrite(os.path.join(OUTPUT_DIR, nome_saida), augmented)

print(f"Concluído! {len(arquivos)} imagens geradas em '{OUTPUT_DIR}'")