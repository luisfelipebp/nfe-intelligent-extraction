from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from models.nota import NotaFiscalInput, NotaFiscalOutput, UploadAceitoResponse
from services.nota_service import buscar_nota_por_chave, criar_nota, buscar_nota_por_id,atualizar_nota_concluida, deletar_nota, buscar_nota_por_id_transacao, listar_notas, criar_nota_pendente
from database import get_db, SessionLocal
from estado import recursos_ia
import re
from fastapi import Query

import tempfile
import os


router = APIRouter()

def processar_nota_background(caminho_arquivo: str, nome_arquivo: str, id_transacao: str):
    db = SessionLocal() 
    
    try:
        extrator_ia = recursos_ia["extrator_nfe"]
        dados_dicionario = extrator_ia.process_file(caminho_arquivo)

        
        if "erro" in dados_dicionario:
            raise ValueError(f"Erro na IA: {dados_dicionario['erro']}")

        dados_formatados = {
            "nome_arquivo": nome_arquivo, 
            "numero": dados_dicionario.get("NUM_NOTA_FISCAL"),
            "serie": dados_dicionario.get("NUM_SERIE"),
            "chave_acesso": dados_dicionario.get("CHAVE_ACESSO"),
            "valor_total": dados_dicionario.get("VALOR_TOTAL"),
        
            "emitente": {
                "razao_social": dados_dicionario.get("NOME_EMITENTE"),
                "cpf_cnpj": dados_dicionario.get("CNPJ_EMITENTE"),
                "tipo_pessoa": inferir_tipo_pessoa(dados_dicionario.get("CNPJ_EMITENTE"))
            },
        
        "destinatario": {
            "razao_social": dados_dicionario.get("NOME_DESTINATARIO"),
            "cpf_cnpj": dados_dicionario.get("CNPJ_DESTINATARIO"),
            "tipo_pessoa": inferir_tipo_pessoa(dados_dicionario.get("CNPJ_DESTINATARIO"))
        }
    }

        
        nota_pydantic = NotaFiscalInput(**dados_formatados)
        
        if buscar_nota_por_chave(db, nota_pydantic.chave_acesso) is not None:
             raise ValueError("Nota fiscal duplicada!")

        atualizar_nota_concluida(db, id_transacao, nota_pydantic)


    except Exception as e:
        print(f"Erro: {e}")
        raise

    finally:
        if caminho_arquivo is not None and os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        db.close() 

def inferir_tipo_pessoa(cpf_cnpj: str | None) -> str:
    if not cpf_cnpj:
        return "PJ"
    return "PF" if len(re.sub(r'\D', '', cpf_cnpj)) == 11 else "PJ"


@router.post("/", response_model=UploadAceitoResponse, status_code=202, summary="Criar nota fiscal",
             description="Recebe os dados de uma nota fiscal, valida e persiste no banco.")
async def upload_criar_nota(arquivo: UploadFile = File(...),background_tasks: BackgroundTasks = BackgroundTasks() ,db: Session = Depends(get_db)):
    
    EXTENSOES_ACEITAS = {".pdf", ".jpg", ".jpeg", ".png"}
    extensao = f".{arquivo.filename.split('.')[-1]}" if "." in arquivo.filename else ".pdf"
    if extensao not in EXTENSOES_ACEITAS:
        raise HTTPException(status_code=415, detail=f"Formato não suportado. Aceitos: {EXTENSOES_ACEITAS}")
    
    arquivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=extensao)
    caminho_arquivo = arquivo_temp.name
    conteudo_em_bytes = await arquivo.read()
    arquivo_temp.write(conteudo_em_bytes)
    arquivo_temp.close() 

    nota_pendente = criar_nota_pendente(db, nome_arquivo=arquivo.filename)

    id_transacao = nota_pendente.id_transacao

    background_tasks.add_task(
        processar_nota_background,
        caminho_arquivo=caminho_arquivo,
        nome_arquivo=arquivo.filename,
        id_transacao=id_transacao
    )

    return {
        "mensagem": "Arquivo recebido e processamento iniciado.",
        "id_transacao": id_transacao,
        "status": "pendente"
    }



@router.get("/{nota_id}",response_model=NotaFiscalOutput,summary="Buscar nota fiscal por ID")
def buscar_nota(nota_id: int,db: Session = Depends(get_db)):
    nota = buscar_nota_por_id(db, nota_id)

    if nota is None:
        raise HTTPException(
            status_code=404,
            detail={
                "erro": "Nota fiscal não foi encontrada",
                "id_consultado": nota_id
            }
        )
    
    return nota



@router.get("/{id_transacao}",response_model=NotaFiscalOutput,summary="Buscar nota fiscal por ID de transacao")
def buscar_nota(id_transacao: str,db: Session = Depends(get_db)):
    nota = buscar_nota_por_id_transacao(db, id_transacao)

    if nota is None:
        raise HTTPException(
            status_code=404,
            detail={
                "erro": "Nota fiscal não foi encontrada",
                "id_consultado": id_transacao
            }
        )
    
    return nota



@router.get("/", response_model=list[NotaFiscalOutput], summary="Listar todas as notas fiscais")
def obter_todas_as_notas(
    skip: int = Query(0, description="Quantos registros pular (para paginação)"),
    limit: int = Query(100, le=500, description="Limite máximo de registros retornados (máximo 500)"),
    db: Session = Depends(get_db)
):
    """
    Retorna uma lista de notas fiscais cadastradas no banco de dados.
    """
    
    notas = listar_notas(db, skip=skip, limit=limit)
    
    return notas



@router.delete(
    "/{nota_id}",
    status_code=204,
    summary="Deletar nota fiscal"
)
def deletar_nota_rota(nota_id: int, db: Session = Depends(get_db)):
    sucesso = deletar_nota(db, nota_id)

    if not sucesso:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")
