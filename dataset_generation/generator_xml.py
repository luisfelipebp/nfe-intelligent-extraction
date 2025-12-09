import os
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from faker import Faker

OUTPUT_DIR = "./generated_xmls/"
FILE_COUNT = 30
fake = Faker('pt_BR')

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

PRODUCTS = [
    "Parafuso Sextavado", "Computador Gamer", "Servico de Manutencao", 
    "Cimento Votoran", "Coca Cola 2L", "Mouse Sem Fio", "Consultoria TI", 
    "Gasolina Aditivada", "Papel A4 500fls", "Caneta Azul", "Teclado Mecanico", 
    "Monitor 24pol", "Agua Mineral", "Cafe Pilao", "Acucar Uniao", "Tijolo"
]

ADJECTIVES = [
    "Alto Desempenho", "Industrial", "Premium", "Modelo 2025", "Importado", 
    "com Garantia", "Reforcado", "Azul", "Vermelho", "Kit Completo", "Simples"
]

def format_value(value):
    return "{:.2f}".format(value)

def generate_entity_doc():
    if random.choice([True, False]):
        doc = fake.cnpj().replace('.', '').replace('/', '').replace('-', '')
        name = fake.company()
        return doc, name, "CNPJ"
    else: 
        doc = fake.cpf().replace('.', '').replace('-', '')
        name = fake.name()
        return doc, name, "CPF"

def create_master_xml(index):
    print_type = random.choice(['1', '1', '1', '2']) 
    
    nfe = ET.Element("NFe", xmlns="http://www.portalfiscal.inf.br/nfe")
    inf_nfe = ET.SubElement(nfe, "infNFe", Id=f"NFe{fake.random_number(digits=44)}", versao="4.00")
    
    ide = ET.SubElement(inf_nfe, "ide")
    ET.SubElement(ide, "cUF").text = "35"
    ET.SubElement(ide, "cNF").text = str(fake.random_number(digits=8))
    ET.SubElement(ide, "natOp").text = random.choice(["VENDA", "PRESTACAO SERVICO", "REMESSA", "DEVOLUCAO"])
    ET.SubElement(ide, "mod").text = "55"
    ET.SubElement(ide, "serie").text = str(random.randint(1, 999))
    ET.SubElement(ide, "nNF").text = str(random.randint(1, 999999))
    
    base_date = datetime.now()
    ET.SubElement(ide, "dhEmi").text = base_date.isoformat()
    ET.SubElement(ide, "dhSaiEnt").text = (base_date + timedelta(hours=random.randint(1, 12))).isoformat()
    
    ET.SubElement(ide, "tpNF").text = random.choice(['0', '1'])
    ET.SubElement(ide, "idDest").text = "1"
    ET.SubElement(ide, "cMunFG").text = "3550308"
    ET.SubElement(ide, "tpImp").text = print_type
    ET.SubElement(ide, "tpEmis").text = "1"
    ET.SubElement(ide, "cDV").text = "0"
    ET.SubElement(ide, "tpAmb").text = "1"
    ET.SubElement(ide, "finNFe").text = "1"
    ET.SubElement(ide, "indFinal").text = "1"
    ET.SubElement(ide, "indPres").text = "1"
    ET.SubElement(ide, "procEmi").text = "0"
    ET.SubElement(ide, "verProc").text = "Generator v1.0"

    emit = ET.SubElement(inf_nfe, "emit")
    doc, name, doc_type = generate_entity_doc()
    ET.SubElement(emit, doc_type).text = doc
    ET.SubElement(emit, "xNome").text = name
    if doc_type == "CNPJ": ET.SubElement(emit, "xFant").text = fake.company_suffix()
    
    addr_emit = ET.SubElement(emit, "enderEmit")
    ET.SubElement(addr_emit, "xLgr").text = fake.street_name()
    ET.SubElement(addr_emit, "nro").text = str(fake.building_number())
    ET.SubElement(addr_emit, "xBairro").text = fake.bairro()
    ET.SubElement(addr_emit, "cMun").text = "3550308"
    ET.SubElement(addr_emit, "xMun").text = fake.city()
    ET.SubElement(addr_emit, "UF").text = fake.state_abbr()
    ET.SubElement(addr_emit, "CEP").text = "01001000"
    ET.SubElement(emit, "IE").text = str(fake.random_number(digits=12))
    ET.SubElement(emit, "CRT").text = "3"

    dest = ET.SubElement(inf_nfe, "dest")
    doc, name, doc_type = generate_entity_doc()
    ET.SubElement(dest, doc_type).text = doc
    ET.SubElement(dest, "xNome").text = name

    addr_dest = ET.SubElement(dest, "enderDest")
    ET.SubElement(addr_dest, "xLgr").text = fake.street_name()
    ET.SubElement(addr_dest, "nro").text = str(fake.building_number())
    ET.SubElement(addr_dest, "xBairro").text = fake.bairro()
    ET.SubElement(addr_dest, "cMun").text = "3550308"
    ET.SubElement(addr_dest, "xMun").text = fake.city()
    ET.SubElement(addr_dest, "UF").text = fake.state_abbr()
    ET.SubElement(addr_dest, "CEP").text = "02002000"

    item_count = random.randint(1, 20)
    total_prod_value = 0.0
    
    for i in range(1, item_count + 1):
        det = ET.SubElement(inf_nfe, "det", nItem=str(i))
        prod = ET.SubElement(det, "prod")
        ET.SubElement(prod, "cProd").text = str(fake.random_number(digits=5))
        ET.SubElement(prod, "cEAN").text = "SEM GTIN"
        
        prod_name = random.choice(PRODUCTS)
        if random.random() < 0.3: prod_name += " " + random.choice(ADJECTIVES)
        ET.SubElement(prod, "xProd").text = prod_name
        
        ET.SubElement(prod, "NCM").text = "00000000"
        ET.SubElement(prod, "CFOP").text = "5102"
        ET.SubElement(prod, "uCom").text = random.choice(["UN", "CX", "KG"])
        
        qty = random.randint(1, 10)
        if random.random() < 0.4:
            unit_price = random.uniform(1.00, 15.00)
        else:
            unit_price = random.uniform(20.00, 1000.00)
            
        prod_val = qty * unit_price
        total_prod_value += prod_val
        
        ET.SubElement(prod, "qCom").text = format_value(qty)
        ET.SubElement(prod, "vUnCom").text = format_value(unit_price)
        ET.SubElement(prod, "vProd").text = format_value(prod_val)
        ET.SubElement(prod, "cEANTrib").text = "SEM GTIN"
        ET.SubElement(prod, "uTrib").text = "UN"
        ET.SubElement(prod, "qTrib").text = format_value(qty)
        ET.SubElement(prod, "vUnTrib").text = format_value(unit_price)
        ET.SubElement(prod, "indTot").text = "1"
        
        tax = ET.SubElement(det, "imposto")
        icms = ET.SubElement(tax, "ICMS")
        icms00 = ET.SubElement(icms, "ICMS00")
        ET.SubElement(icms00, "orig").text = "0"
        ET.SubElement(icms00, "CST").text = "00"
        ET.SubElement(icms00, "modBC").text = "3"
        ET.SubElement(icms00, "vBC").text = format_value(prod_val)
        ET.SubElement(icms00, "pICMS").text = "0.00"
        ET.SubElement(icms00, "vICMS").text = "0.00"

    total = ET.SubElement(inf_nfe, "total")
    icms_tot = ET.SubElement(total, "ICMSTot")
    
    freight_val = random.uniform(5.00, 50.00)
    ipi_val = total_prod_value * 0.05 if random.random() < 0.3 else 0.00
    total_nf_val = total_prod_value + freight_val + ipi_val

    ET.SubElement(icms_tot, "vBC").text = "0.00"
    ET.SubElement(icms_tot, "vICMS").text = "0.00"
    ET.SubElement(icms_tot, "vICMSDeson").text = "0.00"
    ET.SubElement(icms_tot, "vFCP").text = "0.00"
    ET.SubElement(icms_tot, "vBCST").text = "0.00"
    ET.SubElement(icms_tot, "vST").text = "0.00"
    ET.SubElement(icms_tot, "vFCPST").text = "0.00"
    ET.SubElement(icms_tot, "vFCPSTRet").text = "0.00"
    ET.SubElement(icms_tot, "vProd").text = format_value(total_prod_value)
    ET.SubElement(icms_tot, "vFrete").text = format_value(freight_val)
    ET.SubElement(icms_tot, "vSeg").text = "0.00"
    ET.SubElement(icms_tot, "vDesc").text = "0.00"
    ET.SubElement(icms_tot, "vII").text = "0.00"
    ET.SubElement(icms_tot, "vIPI").text = format_value(ipi_val)
    ET.SubElement(icms_tot, "vIPIDevol").text = "0.00"
    ET.SubElement(icms_tot, "vPIS").text = "0.00"
    ET.SubElement(icms_tot, "vCOFINS").text = "0.00"
    ET.SubElement(icms_tot, "vOutro").text = "0.00"
    ET.SubElement(icms_tot, "vNF").text = format_value(total_nf_val)

    transp = ET.SubElement(inf_nfe, "transp")
    ET.SubElement(transp, "modFrete").text = random.choice(['0', '1', '9'])

    billing = ET.SubElement(inf_nfe, "cobr")
    invoice = ET.SubElement(billing, "fat")
    ET.SubElement(invoice, "nFat").text = str(fake.random_number(digits=6))
    ET.SubElement(invoice, "vOrig").text = format_value(total_nf_val)
    ET.SubElement(invoice, "vLiq").text = format_value(total_nf_val)
    
    dup = ET.SubElement(billing, "dup")
    ET.SubElement(dup, "nDup").text = "001"
    ET.SubElement(dup, "dVenc").text = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    ET.SubElement(dup, "vDup").text = format_value(total_nf_val)

    info = ET.SubElement(inf_nfe, "infAdic")
    ET.SubElement(info, "infCpl").text = fake.text().replace("\n", " ")

    proc_nfe = ET.Element('nfeProc', xmlns="http://www.portalfiscal.inf.br/nfe", versao="4.00")
    proc_nfe.append(nfe)
    
    prot_nfe = ET.SubElement(proc_nfe, "protNFe", versao="4.00")
    inf_prot = ET.SubElement(prot_nfe, "infProt")
    ET.SubElement(inf_prot, "tpAmb").text = "1"
    ET.SubElement(inf_prot, "verAplic").text = "App"
    ET.SubElement(inf_prot, "chNFe").text = f"35{fake.random_number(digits=42)}"
    ET.SubElement(inf_prot, "dhRecbto").text = datetime.now().isoformat()
    ET.SubElement(inf_prot, "nProt").text = str(fake.random_number(digits=15))
    ET.SubElement(inf_prot, "digVal").text = "VALIDO"
    ET.SubElement(inf_prot, "cStat").text = "100"
    ET.SubElement(inf_prot, "xMotivo").text = "Autorizado o uso da NF-e"

    tree = ET.ElementTree(proc_nfe)
    filename = os.path.join(OUTPUT_DIR, f"nfe_{index}.xml")
    tree.write(filename, encoding="utf-8", xml_declaration=True)

for f in os.listdir(OUTPUT_DIR):
    os.remove(os.path.join(OUTPUT_DIR, f))

print(f"Gerando {FILE_COUNT} NFe XMLs...")
for i in range(FILE_COUNT):
    create_master_xml(i)
print(f"Sucesso ! Arquivos salvos em '{OUTPUT_DIR}'")