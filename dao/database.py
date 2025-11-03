import os
import time
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()

load_dotenv()

# Verificar se estamos em modo de teste
TESTING = os.getenv("TESTING") == "1"

DATABASE_URL = os.getenv("DATABASE_URL")

if not TESTING and not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida.")

def wait_for_db(db_url: str):
    max_retries = 15
    retry_delay = 3
    retries = 0

    print("Aguardando o banco de dados ficar disponivel...")

    while retries < max_retries:
        try:
            temp_engine = create_engine(db_url, connect_args={"charset": "utf8mb4"})
            with temp_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Conexao com o banco de dados bem-sucedida!")
            return temp_engine
        except OperationalError:
            retries += 1
            print(f"Banco de dados ainda nao esta pronto. Tentando novamente em {retry_delay}s... ({retries}/{max_retries})")
            time.sleep(retry_delay)

    print("Nao foi possivel conectar ao banco de dados apos varias tentativas. Abortando.")
    exit(1)

# Só conectar ao banco se não estivermos em modo de teste
if not TESTING:
    engine = wait_for_db(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # Em modo de teste, criar um engine dummy que será sobrescrito
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    # Em modo de teste, esta função será sobrescrita pela fixture
    # Mas ainda precisa ter uma implementação válida para não quebrar imports
    if SessionLocal is None:
        # Modo de teste - retornar None (será sobrescrito)
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()