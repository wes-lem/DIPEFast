import pymysql
pymysql.install_as_MySQLdb()

import importlib
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# URL de conexão com o banco de dados (MySQL no Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuração do engine SQLAlchemy
# connect_args adicionado para garantir charset no MySQL
engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})

# Criação da sessão
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos declarativos
Base = declarative_base()

# Função para obter a sessão do banco
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

def import_models():
    # Modelos existentes
    Resposta = importlib.import_module("models.resposta")
    Aluno = importlib.import_module("models.aluno")
    Usuario = importlib.import_module("models.usuario")
    Prova = importlib.import_module("models.prova")
    Questao = importlib.import_module("models.questao")
    Resposta = importlib.import_module("models.resposta")
    
    # Novos modelos
    Formulario = importlib.import_module("models.formulario")
    PerguntaFormulario = importlib.import_module("models.pergunta_formulario")
    RespostaFormulario = importlib.import_module("models.resposta_formulario")
    Notificacao = importlib.import_module("models.notificacao")
    
    # Chama a função para garantir que os modelos sejam carregados
    return (
        Resposta, Aluno, Usuario, Prova, Questao,
        Formulario, PerguntaFormulario, RespostaFormulario, Notificacao
    )

import_models()
# Para criação das tabelas no banco de dados
Base.metadata.create_all(bind=engine)