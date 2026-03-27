from sqlalchemy.orm import Session
from models.nota_model import DestinatarioModel

def criar_destinatario(db: Session, nota_id: int, dados) -> DestinatarioModel:
    destinatario = DestinatarioModel(
            razao_social = dados.razao_social,
            cpf_cnpj = dados.cpf_cnpj,
            tipo_pessoa = dados.tipo_pessoa, nota_id = nota_id)
    db.add(destinatario)
    return destinatario


def buscar_nota_por_id(db: Session, nota_id: int) -> DestinatarioModel | None:
    """Busca uma nota pelo ID gerado pelo banco."""
    return db.query(DestinatarioModel).filter(DestinatarioModel.id == nota_id).first()