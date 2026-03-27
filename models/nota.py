from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal


class Emitente(BaseModel):
    razao_social: Optional[str] = Field(None, min_length=2, max_length=100)
    cpf_cnpj: Optional[str] = Field(None, min_length=11, max_length=18)
    tipo_pessoa: Optional[Literal['PJ', 'PF']] = None


class Destinatario(BaseModel):
    razao_social: Optional[str] = Field(None, min_length=2, max_length=100)
    cpf_cnpj: Optional[str] = Field(None, min_length=11, max_length=18)
    tipo_pessoa: Optional[Literal['PJ', 'PF']] = None


class NotaFiscalInput(BaseModel):
    nome_arquivo: str = Field(min_length=5, max_length=100)
    numero: Optional[str] = None
    serie: Optional[str] = None
    chave_acesso: Optional[str] = Field(None, min_length=20, max_length=54)
    emitente: Optional[Emitente] = None
    destinatario: Optional[Destinatario] = None
    data_emissao: Optional[datetime] = None
    valor_total: Optional[float] = None
    moeda: Optional[Literal['BRL', 'EUR', 'USD']] = 'BRL'

    @field_validator("valor_total", mode="before")
    @classmethod
    def limpar_valor_monetario(cls, valor: str):
        if not valor:
            return None
        

        if isinstance(valor, float) or isinstance(valor, int):
            return float(valor)
        
        if isinstance(valor, str):

            try:
                valor_sem_milhar = valor.replace(".", "")
                
                valor_formato_americano = valor_sem_milhar.replace(",", ".")
                
                return float(valor_formato_americano)
                
            except ValueError:
                return None
        return None


class NotaFiscalOutput(BaseModel): 
    id_transacao: str
    nome_arquivo: str
    status: str
    data_processamento: datetime

    numero: Optional[str] = None
    serie: Optional[str] = None
    chave_acesso: Optional[str] = None
    valor_total: Optional[float] = None
    emitente: Optional[Emitente] = None
    destinatario: Optional[Destinatario] = None

    class Config:
        from_attributes = True

class UploadAceitoResponse(BaseModel):
    mensagem: str
    id_transacao: str
    status: str