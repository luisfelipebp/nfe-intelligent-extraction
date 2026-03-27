def nota_payload(chave_acesso: str = "12345678901234567890123456789012345678901234") -> dict:
    """
    Fábrica que simula o Dicionário exato que o seu LayoutLMv3/Extrator devolve.
    Útil para testar se o Pydantic está validando certo e se o banco está salvando.
    """
    return {
        "nome_arquivo": "teste.pdf",
        "NUM_NOTA_FISCAL": "12345",
        "NUM_SERIE": "1",
        "CHAVE_ACESSO": chave_acesso,
        "ID_TRANSACAO": "1230122332039210321",
        "VALOR_TOTAL": "150.00",
        "NOME_EMITENTE": "Empresa Teste LTDA",
        "CNPJ_EMITENTE": "00.000.000/0001-00",
        "NOME_DESTINATARIO": "Felipe Barbosa",
        "CNPJ_DESTINATARIO": "11.111.111/0001-11"
    }