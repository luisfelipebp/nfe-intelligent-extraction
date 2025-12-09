import fitz  # PyMuPDF
import os

dir_pdf = "./generated_pdfs/" 
dir_img = "./generated_images/"

if not os.path.exists(dir_img):
    os.makedirs(dir_img)

print("Iniciando conversão de PDF para Imagem...")

for nome_arquivo in os.listdir(dir_pdf):
    if nome_arquivo.endswith(".pdf"):
        caminho_pdf = os.path.join(dir_pdf, nome_arquivo)

        try:
            doc = fitz.open(caminho_pdf)
            page = doc.load_page(0) 
            
            pix = page.get_pixmap(dpi=300)

            nome_jpg = nome_arquivo.replace(".pdf", ".jpg")
            caminho_jpg = os.path.join(dir_img, nome_jpg)

            pix.save(caminho_jpg, "jpeg")
            print(f"Convertido: {nome_jpg}")

            doc.close()

        except Exception as e:
            print(f"Erro ao converter {nome_arquivo}: {e}")

print("Conversão concluída!")