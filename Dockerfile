# 1. Escolhe a imagem base do Python (usando a versão slim para ficar mais leve)
FROM python:3.12-slim

# 2. Define o diretório de trabalho dentro do container
WORKDIR /app

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# 3. Copia apenas o arquivo de dependências primeiro (isso otimiza o cache do Docker)
COPY requirements.txt .

# 4. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia o resto do código do seu projeto para dentro do container
COPY . .

# 6. Expõe a porta que o FastAPI vai rodar
EXPOSE 8000

# 7. O comando para iniciar a sua aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]