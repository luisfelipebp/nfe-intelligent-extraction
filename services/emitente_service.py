from sqlalchemy.orm import Session
from models.nota_model import EmitenteModel

def criar_emitente(db: Session, nota_id: int, dados) -> EmitenteModel:
    emitente = EmitenteModel(
        nota_id=nota_id,
        razao_social=dados.razao_social,
        cpf_cnpj=dados.cpf_cnpj,
        tipo_pessoa=dados.tipo_pessoa
    )
    db.add(emitente)
    return emitente


def buscar_emitente_por_id(db: Session, emitente_id: int) -> EmitenteModel | None:
    """Busca uma nota pelo ID gerado pelo banco."""
    return db.query(EmitenteModel).filter(EmitenteModel.id == emitente_id).first()