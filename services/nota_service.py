from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from models.nota_model import NotaModel, EmitenteModel, DestinatarioModel
from models.nota import NotaFiscalInput
from services.destinatario_service import criar_destinatario
from services.emitente_service import criar_emitente
import uuid

def criar_nota(db: Session, nota_input: NotaFiscalInput) -> NotaModel:

    nova_nota = NotaModel(
        nome_arquivo= nota_input.nome_arquivo,
        numero = nota_input.numero,
        serie = nota_input.serie,
        chave_acesso = nota_input.chave_acesso,
        data_emissao = nota_input.data_emissao,
        valor_total = nota_input.valor_total,
        moeda = nota_input.moeda)
    

    db.add(nova_nota)
    db.flush()
    
    if nota_input.emitente:
        criar_emitente(db, nova_nota.id, nota_input.emitente)
    if nota_input.destinatario:
        criar_destinatario(db, nova_nota.id, nota_input.destinatario)
    
    db.commit()

    db.refresh(nova_nota)
    return nova_nota

def buscar_nota_por_chave(db: Session, nota_chave_acesso: int) -> NotaModel | None:
    """Busca uma nota pelo ID gerado pelo banco."""
    return db.query(NotaModel).filter(NotaModel.chave_acesso == nota_chave_acesso).first()


def buscar_nota_por_id(db: Session, nota_id: int) -> NotaModel | None:
    """Busca uma nota pelo ID gerado pelo banco."""
    return db.query(NotaModel).filter(NotaModel.id == nota_id).first()    


def buscar_nota_por_id_transacao(db: Session, id_transacao: str) -> NotaModel | None:
    """Busca uma nota pelo ID gerado pelo banco."""
    return db.query(NotaModel).filter(NotaModel.id_transacao == id_transacao).first() 


def listar_notas_filtradas(
    db: Session,
    status: str | None = None,
    valor_minimo: float | None = None,
    emitente: str | None = None
) -> list[NotaModel]:
    """
    Lista notas com filtros opcionais.
    Cada filtro só é aplicado se o valor for passado — None significa "sem filtro".
    """
    query = db.query(NotaModel)

    if status:
        query = query.filter(NotaModel.status == status)

    if valor_minimo:
        query = query.filter(NotaModel.valor_total >= valor_minimo)

    if emitente:
        query = query.filter(NotaModel.emitente.ilike(f"%{emitente}%"))

    return query.order_by(desc(NotaModel)).all()


def listar_notas(db: Session, skip: int = 0, limit: int = 100) -> list[NotaModel]:
    """
    Lista notas com paginação.
    skip → quantos registros pular (offset)
    limit → quantos registros retornar no máximo
    """
    return db.query(NotaModel).offset(skip).limit(limit).all()


def deletar_nota(db: Session, nota_id: int) -> bool:
    """
    Deleta uma nota e seus itens (cascade).
    Retorna True se deletou, False se não encontrou.
    """
    nota = buscar_nota_por_id(db, nota_id)

    if nota is None:
        return False

    db.delete(nota)
    db.commit()
    return True


def contar_notas(db: Session) -> int:
    """Retorna o total de notas no banco."""
    return db.query(func.count(NotaModel.id)).scalar()


def criar_nota_pendente(db: Session, nome_arquivo: str):
    """
    Cria o registro inicial no banco em frações de segundo.
    O resto das colunas ficará vazio (NULL) por enquanto.
    """
    novo_id_transacao = str(uuid.uuid4())
    
    nova_nota = NotaModel(
        id_transacao=novo_id_transacao,
        nome_arquivo=nome_arquivo,
        status="pendente"
    )
    
    db.add(nova_nota)
    db.commit()
    db.refresh(nova_nota) 
    
    return nova_nota


def atualizar_nota_concluida(db: Session, id_transacao: str, nota_pydantic: NotaFiscalInput):
    """
    Busca a nota pendente e preenche com os dados reais da extração.
    """
    nota_no_banco = db.query(NotaModel).filter(NotaModel.id_transacao == id_transacao).first()
    
    if nota_no_banco:
        nota_no_banco.numero = nota_pydantic.numero
        nota_no_banco.serie = nota_pydantic.serie
        nota_no_banco.chave_acesso = nota_pydantic.chave_acesso
        nota_no_banco.valor_total = nota_pydantic.valor_total
        
        if nota_pydantic.emitente:
            criar_emitente(db, nota_no_banco.id, nota_pydantic.emitente)
        if nota_pydantic.destinatario:
            criar_destinatario(db, nota_no_banco.id, nota_pydantic.destinatario)
            
        nota_no_banco.status = "concluido"
        
        db.commit()
        db.refresh(nota_no_banco)
        
    return nota_no_banco
        