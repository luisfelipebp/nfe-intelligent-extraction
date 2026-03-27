from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import uuid


class EmitenteModel(Base):
    __tablename__ = "emitente"

    id = Column(Integer, primary_key=True, index=True)

    razao_social = Column(String, nullable=True)
    cpf_cnpj = Column(String, nullable=True)
    tipo_pessoa = Column(Enum('PJ', 'PF', name='emitente_tipo_enum'), default="PF", nullable=False)

    nota_id = Column(Integer, ForeignKey("notas.id", ondelete="CASCADE"), nullable=False)

    nota = relationship("NotaModel", back_populates="emitente")


class DestinatarioModel(Base):
    __tablename__ = "destinatario"

    id = Column(Integer, primary_key=True, index=True)

    razao_social = Column(String, nullable=True)
    cpf_cnpj = Column(String, nullable=True)
    tipo_pessoa = Column(Enum('PJ', 'PF', name='destinatario_tipo_enum'),default="PJ", nullable=False)

    nota_id = Column(Integer, ForeignKey("notas.id", ondelete="CASCADE"), nullable=False)

    nota = relationship("NotaModel", back_populates="destinatario")


class NotaModel(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)

    id_transacao = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, nullable=False)
    data_processamento = Column(DateTime, default=datetime.now)
    nome_arquivo = Column(String, nullable=False)

    numero = Column(String, nullable=True)
    serie = Column(String, nullable=True)
    chave_acesso = Column(String, unique=True, index=True, nullable=True)
    data_emissao = Column(DateTime, nullable=True)

    valor_total = Column(Float, nullable=True)
    moeda = Column(Enum('BRL', 'EUR', 'USD', name='moeda_enum'), default='BRL')

    
    emitente = relationship("EmitenteModel", back_populates="nota", cascade="all, delete-orphan", uselist=False)
    destinatario = relationship("DestinatarioModel", back_populates="nota", cascade="all, delete-orphan", uselist=False)