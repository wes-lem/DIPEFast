# Usa a imagem oficial do Python na versão 3.13 como base
FROM python:3.13

# Define o diretório de trabalho dentro do container como /app
WORKDIR /app

# Copia apenas o arquivo requirements.txt para dentro do container
COPY requirements.txt .

# Instala as dependências do projeto sem armazenar cache
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo do diretório atual para dentro do diretório /app no container
COPY . .

# Expõe a porta 8080 para que o container possa receber conexões externas
EXPOSE 8080

# Inicia o servidor Uvicorn, rodando a aplicação definida em "main.py"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]