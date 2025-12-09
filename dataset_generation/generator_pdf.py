import os
from brazilfiscalreport.danfe import Danfe

INPUT_DIR = "./generated_xmls/"
OUTPUT_DIR = "./generated_pdfs/"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("Iniciando conversão de XML para PDF...")

files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xml")]

for filename in files:
    xml_path = os.path.join(INPUT_DIR, filename)
    
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        danfe = Danfe(xml=xml_content)
        
        pdf_filename = filename.replace(".xml", ".pdf")
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        
        danfe.output(pdf_path)
        
        print(f"Gerado: {pdf_filename}")
        
    except Exception as e:
        print(f"Erro ao processar {filename}: {e}")

print(f"Processo concluído! {len(files)} arquivos verificados.")