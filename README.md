# NFe Intelligent Extraction — IDP com LayoutLMv3 + API REST

> Solução completa de **Intelligent Document Processing (IDP)** para extração automatizada de dados estruturados de Notas Fiscais Eletrônicas (DANFEs), com backend profissional pronto para produção.

---

## Visão Geral

Este projeto combina **Deep Learning Multimodal** com uma **API REST robusta**, entregando um serviço end-to-end que:

1. Recebe o upload de uma imagem ou PDF de DANFE
2. Processa o documento com um modelo LayoutLMv3 fine-tuned
3. Retorna os dados estruturados em JSON
4. Persiste os resultados em banco de dados relacional

---

## O Problema: Por que OCR tradicional falha em DANFEs

A extração confiável de DANFEs é um desafio porque:

- **Layout variável** — cada emitente organiza as informações de forma diferente. Soluções baseadas em templates falham com emitentes novos
- **Qualidade de imagem** — digitalizações tortas ou com baixa resolução comprometem o reconhecimento
- **Ambiguidade numérica** — existem vários números semelhantes no documento (CNPJs diferentes, valores unitários vs. valor total) e o OCR sozinho não distingue qual é qual sem entender o contexto visual

---

## Arquitetura da Solução: LayoutLMv3

O modelo central é o **LayoutLMv3 (Microsoft)**, que combina três fontes de informação simultaneamente:

| Fonte | O que contribui |
|---|---|
| Imagem completa | Estrutura visual, tabelas, alinhamentos |
| Texto via OCR | Conteúdo textual bruto |
| Posição dos tokens | Relações espaciais — "valor à direita do rótulo TOTAL" |

Essa fusão multimodal permite identificar campos corretamente mesmo em layouts que o modelo nunca viu durante o treino.

---

## Pipeline de Machine Learning

### 1. Engenharia de Dados — Geração Sintética

Como notas fiscais reais contêm dados sensíveis (LGPD), toda a base de treino foi gerada sinteticamente:

- Scripts Python com `Faker` para gerar dados aleatórios e renderizar DANFEs (Modelo 55)
- Aplicação de efeitos para simular condições reais: ruído, rotação, variação de fontes e resolução

### 2. Anotação de Dados — Data Labeling

Rotulagem manual via **Label Studio**:

- Bounding boxes desenhadas em volta de cada campo relevante
- O modelo aprende não só o conteúdo textual, mas a posição espacial típica de cada informação

### 3. Treinamento — Fine-Tuning

- Modelo base: `microsoft/layoutlmv3-base`
- Stack: PyTorch + HuggingFace Transformers
- Fine-tuning com as DANFEs sintéticas rotuladas

### 4. Lógica de Inferência e Pós-processamento

O script `extractor.py` aplica correções sobre a saída bruta do modelo:

- **Resgate da chave de acesso** — lógica espacial que reconstrói os 44 dígitos quando o OCR os separa em blocos distantes
- **Correção de encoding** — corrige automaticamente erros de acentuação comuns em leitura de imagem (ex: `Bã¡Rbara` → `Bárbara`)
- **Recuperação de valor total** — fallback que varre todos os valores monetários do documento e retorna o maior quando o modelo falha

---

## Stack do Backend

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Validação | Pydantic v2 |
| Banco (dev) | SQLite |
| Banco (prod) | PostgreSQL |
| Testes | Pytest + TestClient |
| Container | Docker + Docker Compose |

---

## Estrutura do Projeto

```
nfe-intelligent-extraction/
│
├── dataset_generation/         # Geração de DANFEs sintéticas (Faker)
├── training/                   # Fine-tuning do LayoutLMv3
├── label_studio_backend/       # Configuração da ferramenta de anotação
├── inference/                  # Modelo treinado e utilitários de pós-processamento
│
├── main.py                     # Inicialização da API e lifespan do modelo
├── database.py                 # Engine, SessionLocal, Base, get_db
├── estado.py                   # Estado global — carregamento único do modelo
│
├── models/
│   ├── nota.py                 # Modelos Pydantic — validação de entrada e saída
│   └── nota_model.py           # Modelos SQLAlchemy — tabelas do banco
│
├── routers/
│   └── notas.py                # Endpoints HTTP
│
├── services/
│   ├── nota_service.py         # CRUD de notas
│   ├── emitente_service.py     # CRUD de emitentes
│   ├── destinatario_service.py # CRUD de destinatários
│   └── extractor.py            # Motor de inferência — LayoutLMv3
│
├── tests/                      # Testes automatizados
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Endpoints da API

### `POST /notas/`
Recebe o upload de uma DANFE e retorna os dados extraídos.

**Request:** `multipart/form-data` com o campo `arquivo` (`.jpg`, `.jpeg`, `.png`, `.pdf`)

**Response `201`:**
```json
{
  "id_transacao": "550e8400-e29b-41d4-a716-446655440000",
  "nome_arquivo": "nfe_0.jpg",
  "status": "sucesso",
  "data_processamento": "2026-03-10T16:40:21.111135",
  "numero": "000885807",
  "serie": "423",
  "chave_acesso": "1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234",
  "valor_total": 23257.43,
  "emitente": {
    "razao_social": "Empresa Emitente LTDA",
    "cpf_cnpj": "XX.XXX.XXX/XXXX-XX",
    "tipo_pessoa": "PJ"
  },
  "destinatario": {
    "razao_social": "Empresa Destinatária LTDA",
    "cpf_cnpj": "XX.XXX.XXX/XXXX-XX",
    "tipo_pessoa": "PJ"
  }
}
```

**Erros possíveis:**

| Status | Situação |
|---|---|
| 415 | Formato de arquivo não suportado |
| 409 | Nota já registrada (chave de acesso duplicada) |
| 422 | Chave de acesso inválida ou campos com formato incorreto |
| 400 | Falha interna no modelo de IA |
| 500 | Erro inesperado no servidor |

---

## Decisões Técnicas Relevantes

**Carregamento único do modelo**
O `NFeProcessor` é instanciado uma única vez no `lifespan` do FastAPI e compartilhado via `estado.py`. Carregar o modelo a cada requisição levaria segundos e tornaria a API inutilizável.

**Arquivo temporário com limpeza garantida**
O arquivo enviado é salvo em disco temporariamente para o modelo processar. O bloco `finally` garante a remoção mesmo que ocorra erro — sem vazamento de arquivos no servidor.

**Separação emitente/destinatário em tabelas próprias**
Os mesmos CNPJs aparecem em múltiplas notas. Tabelas separadas com FK evitam duplicação e permitem consultas como "todas as notas desse emitente".

**Validação de valor monetário no Pydantic**
O modelo retorna valores como `"23.257,43"` (formato BR). Um `field_validator` converte para `float` antes de salvar, sem exigir tratamento manual na rota.

---

## Instalação e Execução

### Com Docker (recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/luisfelipebp/nfe-intelligent-extraction.git
cd nfe-intelligent-extraction

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. Suba os serviços
docker-compose up -d --build

# 4. Acesse a documentação interativa
# http://localhost:8000/docs
```

**Com GPU (10x mais rápido):**
```bash
docker run --gpus all -p 8000:8000 luisfelipebp/nfe-extractor:v1.2
```

**Apenas CPU:**
```bash
docker run -p 8000:8000 luisfelipebp/nfe-extractor:v1.2
```

### Instalação manual (desenvolvimento)

```bash
# 1. Clone e entre na pasta
git clone https://github.com/luisfelipebp/nfe-intelligent-extraction.git
cd nfe-intelligent-extraction

# 2. Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis
cp .env.example .env

# 5. Rode a API
uvicorn main:app --reload
```

### Rodando os testes

```bash
pytest -v

# Com cobertura de código
pytest --cov=. tests/
```

---

## Nota sobre o Modelo Treinado

O arquivo do modelo (`/inference/layoutlmv3-finetuned-nfe`) ultrapassa o limite de 100MB do GitHub e não está incluído no repositório.

| Objetivo | Como proceder |
|---|---|
| Testar agora | Use a imagem Docker — já vem com o modelo incluído |
| Reproduzir o treino | Use os scripts da pasta `/training` |
| Entender a arquitetura | O código está completo e documentado |

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```env
DATABASE_URL=postgresql://postgres:senha@db:5432/nfe
SECRET_KEY=sua-chave-secreta
DEBUG=false
```

---

## Requisitos

- Python 3.11+
- Docker Desktop
- NVIDIA GPU + CUDA (opcional — acelera o processamento em ~10x)
