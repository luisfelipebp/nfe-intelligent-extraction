import pytest
from services.nota_service import atualizar_nota_concluida, criar_nota_pendente
from routers.notas import processar_nota_background
from tests.helpers import nota_payload
from models.nota import NotaFiscalInput 
from routers.notas import recursos_ia


from unittest.mock import patch, MagicMock

def test_criar_nota_sucesso(client):

    payload_arquivo = {
        "arquivo": ("nota.pdf", b"conteudo_falso", "application/pdf")
    }

    response = client.post("/notas", files=payload_arquivo)

    assert response.status_code == 202
    data = response.json()
    assert data["mensagem"] == "Arquivo recebido e processamento iniciado."
    assert data["status"] == "pendente" 
    
    assert "id_transacao" in data



def test_nota_concluida_com_sucesso(db):
    payload = nota_payload()

    payload_validado = NotaFiscalInput(**payload)
    nota_criada = criar_nota_pendente(db, nome_arquivo=payload_validado.nome_arquivo)

    id_falso = nota_criada.id_transacao

    response = atualizar_nota_concluida(db, id_transacao=id_falso, nota_pydantic=payload_validado)

    assert response.id_transacao == id_falso
    assert response.status == "concluido"



@patch.dict("routers.notas.recursos_ia", clear=True)
def test_criar_nota_duplicada_retorna_409(db):

    mock_extrator = MagicMock()
    mock_extrator.process_file.return_value = {
        "NUM_NOTA_FISCAL": "123",
        "NUM_SERIE": "1",
        "CHAVE_ACESSO": "111222333444555666666666",
        "VALOR_TOTAL": 100.0,
        "NOME_EMITENTE": "Empresa Teste",
        "CNPJ_EMITENTE": "00000000000100",
        "NOME_DESTINATARIO": "Cliente Teste",
        "CNPJ_DESTINATARIO": "00000000000200"
    }
    
    recursos_ia["extrator_nfe"] = mock_extrator

    open("temp1.pdf", "w").close()
    open("temp2.pdf", "w").close()

    processar_nota_background(
        caminho_arquivo="temp1.pdf", 
        nome_arquivo="nota1.pdf", 
        id_transacao="ID_1"
    )

    with pytest.raises(ValueError, match="Nota fiscal duplicada!"):
        processar_nota_background(
            caminho_arquivo="temp2.pdf", 
            nome_arquivo="nota2.pdf", 
            id_transacao="ID_2"
        )

















# def test_criar_nota_emitente_com_numero_retorna_422(client):
#     # Arrange
#     payload = nota_payload()
#     payload["emitente"] = "Empresa123"  # inválido pelo field_validator

#     # Act
#     response = client.post("/notas/", json=payload)

#     # Assert
#     assert response.status_code == 422
