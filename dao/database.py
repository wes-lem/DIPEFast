import importlib
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração do banco de dados MySQL
DATABASE_URL = "mysql://root:ExbwVtQWJYneeCoMQqoJCymtxtZvDoIP@ballast.proxy.rlwy.net:59540/railway"

# Criação do engine do SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})

# Sessão local para o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()


# Função para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_models():
    Resposta = importlib.import_module("models.resposta")
    Aluno = importlib.import_module("models.aluno")
    Usuario = importlib.import_module("models.usuario")
    Prova = importlib.import_module("models.prova")
    Questao = importlib.import_module("models.questao")
    Resposta = importlib.import_module("models.resposta")
    # Chama a função para garantir que os modelos sejam carregados
    return Resposta, Aluno, Usuario, Prova, Questao

import_models()
# Para criação das tabelas no banco de dados
Base.metadata.create_all(bind=engine)