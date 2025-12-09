import re
import uuid
from datetime import datetime

def convert_date_iso(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        return date_str

def convert_value_float(value_str):
    try:
        if isinstance(value_str, float): return value_str
        clean = value_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(clean)
    except:
        return 0.00

def clean_field(label, text):
    text = text.replace("\n", " ").strip()
    
    if label == "NUM_NOTA_FISCAL":
        match = re.findall(r'\d{3}\.?\d{3}\.?\d{3}', text)
        if match: return match[0]
        return re.sub(r'[^\d.]', '', text)
    
    if label == "NUM_SERIE":
        text = text.replace('O', '0').replace('o', '0')
        nums = re.sub(r'[^\d]', '', text)
        if len(nums) > 3: return nums[-3:]
        return nums
    
    if label == "VALOR_TOTAL":
        text = re.sub(r'\d{2}[:.]\d{2}[:.]\d{2}', '', text) 
        match = re.search(r'(\d{1,3}(?:[., ]\d{3})*[., ]\d{2})\b', text)
        if match:
            value = match.group(1)
            if '.' in value and ',' not in value: value = value.replace('.', ',')
            return value
        return ""
    
    if label == "CHAVE_ACESSO":
        clean = re.sub(r'\D', '', text)
        if len(clean) >= 44:
            clean = clean[:44]
            return ' '.join([clean[i:i+4] for i in range(0, len(clean), 4)])
        return clean
    
    if "CNPJ" in label:
        nums = re.sub(r'\D', '', text)
        if len(nums) >= 14: return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:14]}"
        if len(nums) >= 11: return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:11]}"
        return text
    
    if "NOME" in label:
        for p in ["Venda", "Natureza", "Fone", "CNPJ", "CPF", "Inscr", "Endereço", "enda ", "Data"]:
            if p.lower() in text.lower(): text = re.split(f"(?i){p}", text)[-1]
        return re.sub(r'^[^a-zA-Z0-9]+', '', text).strip()
    
    if "DATA" in label:
        match = re.search(r'\d{2}\s*/\s*\d{2}\s*/\s*\d{4}', text)
        if match: return match.group(0).replace(" ", "")
        return text
        
    return text

def format_output(filename, raw_data):
    if "erro" in raw_data:
        return {
            "metadados": {
                "arquivo": filename, 
                "status": "erro", 
                "mensagem": raw_data["erro"],
                "data_processamento": datetime.now().isoformat()
            }
        }

    issuer_doc = re.sub(r'\D', '', raw_data.get("CNPJ_EMITENTE", ""))
    recipient_doc = re.sub(r'\D', '', raw_data.get("CNPJ_DESTINATARIO", ""))
    
    issuer_type = "PJ" if len(issuer_doc) > 11 else "PF"
    recipient_type = "PJ" if len(recipient_doc) > 11 else "PF"

    return {
        "metadados": {
            "id_transacao": str(uuid.uuid4()),
            "data_processamento": datetime.now().isoformat(),
            "arquivo_origem": filename,
            "status": "sucesso"
        },
        "nfe": {
            "informacoes_gerais": {
                "numero": re.sub(r'\D', '', raw_data.get("NUM_NOTA_FISCAL", "")),
                "serie": raw_data.get("NUM_SERIE", ""),
                "chave_acesso": raw_data.get("CHAVE_ACESSO", "").replace(" ", ""),
                "data_emissao": convert_date_iso(raw_data.get("DATA_EMISSAO", ""))
            },
            "emitente": { 
                "razao_social": raw_data.get("NOME_EMITENTE", "").upper(),
                "cpf_cnpj": issuer_doc,
                "tipo_pessoa": issuer_type
            },
            "destinatario": { 
                "nome": raw_data.get("NOME_DESTINATARIO", "").title(),
                "cpf_cnpj": recipient_doc,
                "tipo_pessoa": recipient_type
            },
            "financeiro": {
                "valor_total": convert_value_float(raw_data.get("VALOR_TOTAL", "0")),
                "moeda": "BRL"
            }
        }
    }