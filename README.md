# NFe Intelligent Extraction: End-to-End IDP com LayoutLMv3


Este projeto é uma solução completa de **Intelligent Document Processing (IDP)** criada para automatizar a extração de dados estruturados de **Notas Fiscais Eletrônicas (DANFEs)**.

O sistema utiliza uma abordagem de **Deep Learning Multimodal**, capaz de identificar campos importantes como CNPJ, valores, datas e chave de acesso analisando ao mesmo tempo o texto e a estrutura visual do documento.

---

## Problemas do OCR Tradicional

A extração confiável de informações em DANFEs é um desafio porque:

* **Layout variável:** Cada empresa organiza as informações de forma diferente. Soluções que dependem de posições fixas (templates) normalmente falham.
* **Qualidade da imagem:** Digitalizações tortas ou borradas atrapalham o reconhecimento dos caracteres.
* **Contexto visual:** Existem vários números parecidos (ex.: diferentes CNPJs, valores unitários vs. valor total) e o OCR sozinho não sabe qual é qual sem entender a posição e o contexto.

---

## Arquitetura da Solução: LayoutLMv3

A solução utiliza o **LayoutLMv3**, modelo da Microsoft que combina três fontes de informação:

1.  **Imagem completa do documento:** Ajuda a entender tabelas, alinhamentos e estruturas visuais.
2.  **Texto extraído pelo OCR:** O conteúdo textual bruto.
3.  **Posição dos tokens:** Permite que o modelo aprenda relações espaciais, como "o valor que está alinhado à direita do rótulo TOTAL".

Essa integração permite que o sistema identifique corretamente campos mesmo com layouts diferentes.

---

## Pipeline de Machine Learning

O projeto cobre todo o ciclo de desenvolvimento, da criação dos dados até o produto final:

### 1. Engenharia de Dados (Geração de Dados Sintéticos)
Como não é possível utilizar notas fiscais reais de empresas por questões de privacidade (LGPD), criei minha própria base de dados.
* **Gerador:** Criei scripts em Python usando a biblioteca `Faker` para gerar dados aleatórios e desenhar as notas fiscais (focado no Modelo 55/DANFE).
* **Simulação da Realidade:** O gerador aplica efeitos para imitar fotos reais, como ruído, rotação e variação de fontes.

### 2. Anotação de Dados (Data Labeling)
Para ensinar o modelo, precisei mostrar a ele onde estava cada informação. Fiz isso manualmente usando o **Label Studio**.
* **Marcação Visual:** Desenhei as caixas (Bounding Boxes) em volta de cada texto. Isso serve para o modelo aprender não só *o que* está escrito, mas *onde* a informação costuma aparecer na página.

### 3. Treinamento (Fine-Tuning)
Utilizei o **LayoutLMv3 (Microsoft)**.
* **Processo:** Peguei o modelo pré-treinado e fiz o ajuste fino (*fine-tuning*) usando as minhas notas fiscais sintéticas.
* **Tecnologia:** O treinamento foi feito com `PyTorch` e `Transformers`.

### 4. Lógica de Inferência e Correções
Como o modelo de IA pode cometer pequenos erros, criei um script em Python (`inference.py`) para revisar e corrigir os dados:
* **Resgate da Chave de Acesso:** Às vezes o OCR separa os 44 números da chave em blocos distantes. Criei uma lógica que analisa a posição dos números e os "costura" de volta.
* **Correção de Texto:** Uma função que arruma automaticamente erros de acentuação comuns na leitura de imagens (ex: corrige `Bã¡Rbara` para `Bárbara`).
* **União de Valores:** O código junta partes de números decimais que foram quebrados incorretamente.

---

## Estrutura do Projeto

A organização do repositório reflete o pipeline de Engenharia de Machine Learning:

```text
nfe-intelligent-extraction/
│
├── dataset_generation/       # Módulo de Engenharia de Dados
│                             # Contém os scripts (Faker) para gerar as DANFEs sintéticas.
│
├── inference/                # Módulo de Produtização (App Final)
│                             # Contém a aplicação Streamlit, o motor de inferência (inference.py),
│                             # o Dockerfile e as regras de pós-processamento.
│
├── label_studio_backend/     # Configuração de Rotulagem
│                             # Arquivos de suporte para o backend da ferramenta de anotação.
│
├── training/                 # Módulo de Treinamento
│                             # Notebooks e scripts utilizados para o fine-tuning do LayoutLMv3.
│
└── README.md                 # Documentação do projeto
```

---

## Instalação e Execução

O sistema é distribuído em container para garantir que rode igual em qualquer máquina.

### Pré-requisitos
* Docker Desktop instalado.
* (Opcional) Placa de vídeo NVIDIA com drivers atualizados.

### Executar com Docker

**Opção 1: Com GPU (Alta Performance)**
Ideal se você tem uma placa NVIDIA. O processamento é cerca de 10x mais rápido.

> **Requisito CUDA:** Para usar a flag `--gpus all`, certifique-se de ter o **NVIDIA Container Toolkit** instalado.

```bash
docker run --gpus all -p 8501:8501 luisfelipebp/nfe-extractor:v1.1
```

**Opção 2: Apenas CPU (Modo Compatibilidade)**
Funciona em qualquer computador.

```bash
docker run -p 8501:8501 luisfelipebp/nfe-extractor:v1.1
```

### Utilizando a Aplicação
1. Após rodar o comando, abra no navegador: `http://localhost:8501`
2. Envie uma imagem ou PDF de uma **DANFE (Nota Fiscal de Produto)**.
3. O sistema retornará os dados estruturados em JSON.

---

## Instalação Manual (Desenvolvimento)

Caso queira rodar o código fonte localmente ou explorar os notebooks de treino:

### 1. Clone o repositório
```bash
git clone https://github.com/luisfelipebp/nfe-intelligent-extraction.git
cd nfe-intelligent-extraction
```

### 2. Instale as Dependências
```bash
pip install -r inference/requirements.txt
```

### Nota sobre o Modelo Treinado
Como o arquivo do modelo (`/layoutlmv3-finetuned-nfe`) é muito pesado e ultrapassa o limite de 100MB do GitHub, ele **não está incluído** neste repositório.

O que isso significa:
1. **Para rodar no seu PC:** O código `inference.py` só vai funcionar se você treinar seu próprio modelo (usando os scripts da pasta `/training`) ou se tiver o arquivo do modelo salvo manualmente.
2. **Objetivo do Repositório:** Este código serve para demonstrar a arquitetura, a organização e a lógica utilizada no projeto.
3. **Para Testar Agora:** Se quiser ver o projeto funcionando imediatamente sem precisar treinar nada, utilize o **Docker** (comando acima). A imagem Docker já vem com o modelo pronto para uso.

### 3. Executar a Aplicação (Localmente)
Caso você tenha treinado o modelo e gerado os arquivos necessários na pasta correta, execute:

```bash
streamlit run inference/app.py
```

---

## Licença
Este projeto é Open Source sob a **licença MIT**.
O código fonte está disponível livremente para fins educacionais, de portfólio e referência técnica.
