"""
Configuração global de testes com pytest.
Define fixtures compartilhadas para todos os testes.
"""
import pytest
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path do Python
# Isso permite que os testes importem módulos como 'dao', 'controllers', etc.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configurar banco de dados de teste (SQLite em memória)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco de dados de teste isolada para cada teste."""
    # Importar Base após configurar o path
    from dao.database import Base
    
    # Importar TODOS os modelos para garantir que as tabelas sejam criadas
    # Isso é necessário para que SQLAlchemy registre todos os metadados
    from models import usuario, aluno, professor, gestor, turma, campus
    from models import formulario, banco_questoes, prova, questao, resposta
    from models import resultado, notificacao, notificacao_professor
    from models import aluno_turma, prova_turma, prova_questao
    from models import pergunta_formulario, resposta_formulario
    
    # Criar engine de teste com SQLite em memória
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Criar sessão
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Cria um cliente de teste para a aplicação FastAPI."""
    import os
    
    # Configurar variável de ambiente para modo teste (evita conexão com banco real)
    # IMPORTANTE: Fazer isso ANTES de importar qualquer módulo que use database
    original_testing = os.environ.get('TESTING')
    original_db_url = os.environ.get('DATABASE_URL')
    
    os.environ['TESTING'] = '1'
    # DATABASE_URL pode não existir em testes, então não precisamos mockar
    
    try:
        # Importar aqui para garantir que o path está configurado
        from dao.database import get_db
        
        # Importar app depois de configurar o path
        # Importar de forma que não execute código de inicialização
        from fastapi import FastAPI, Request
        from fastapi.staticfiles import StaticFiles
        from controllers.usuario_controller import router as usuario_router
        from controllers.aluno_controller import router as aluno_router
        from controllers.prova_controller import router as prova_router
        from controllers.gestor_controller import router as gestor_router
        from controllers.formulario_controller import router as formulario_router
        from controllers.professor_controller import router as professor_router
        from starlette.exceptions import HTTPException as StarletteHTTPException
        from starlette.exceptions import HTTPException
        from app_config import templates
        
        # Criar app sem inicializar banco
        app = FastAPI()
        app.mount("/static", StaticFiles(directory="templates/static"), name="static")
        
        @app.get("/")
        def home(request: Request):
            return templates.TemplateResponse("index.html", {"request": request})
        
        @app.get("/healthz")
        def health_check():
            return {"status": "ok"}
        
        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            referer_url = request.headers.get("referer")
            back_url = referer_url or "/"
            return templates.TemplateResponse(
                "erro.html",
                {
                    "request": request,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "back_url": back_url
                },
                status_code=exc.status_code
            )
        
        # Incluir rotas
        app.include_router(aluno_router)
        app.include_router(usuario_router)
        app.include_router(prova_router)
        app.include_router(gestor_router)
        app.include_router(formulario_router)
        app.include_router(professor_router)
        
        # Sobrescrever a dependência get_db para usar o banco de teste
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        yield client
        
        # Limpar após o teste
        app.dependency_overrides.clear()
    finally:
        # Restaurar variável de ambiente original
        if original_testing:
            os.environ['TESTING'] = original_testing
        elif 'TESTING' in os.environ:
            del os.environ['TESTING']
        
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        elif 'DATABASE_URL' in os.environ and not original_db_url:
            # Não remover se não tinha antes, pois pode ser necessário para outros testes
            pass

@pytest.fixture
def usuario_aluno(db_session):
    """Cria um usuário do tipo aluno para testes."""
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    
    usuario = Usuario(
        email="aluno_teste@teste.com",
        senha_hash=criptografar_senha("senha123"),
        tipo="aluno"
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario

@pytest.fixture
def usuario_professor(db_session):
    """Cria um usuário do tipo professor para testes."""
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    
    usuario = Usuario(
        email="professor_teste@teste.com",
        senha_hash=criptografar_senha("senha123"),
        tipo="professor"
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario

@pytest.fixture
def usuario_gestor(db_session):
    """Cria um usuário do tipo gestor para testes."""
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    
    usuario = Usuario(
        email="gestor_teste@teste.com",
        senha_hash=criptografar_senha("senha123"),
        tipo="gestor"
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario

@pytest.fixture
def aluno_completo(db_session, usuario_aluno):
    """Cria um aluno completo com todos os dados para testes."""
    from models.aluno import Aluno
    
    aluno = Aluno(
        idUser=usuario_aluno.id,
        nome="Aluno Teste",
        curso="Redes de Computadores",
        ano=1,
        idade=20,
        municipio="Fortaleza",
        zona="urbana",
        origem_escolar="pública"
    )
    db_session.add(aluno)
    db_session.commit()
    db_session.refresh(aluno)
    return aluno

@pytest.fixture
def campus_teste(db_session):
    """Cria um campus de teste."""
    from models.campus import Campus
    
    campus = Campus(
        nome="Campus Teste",
        endereco="Rua Teste, 123",
        ativo=True
    )
    db_session.add(campus)
    db_session.commit()
    db_session.refresh(campus)
    return campus

@pytest.fixture
def professor_completo(db_session, usuario_professor, campus_teste):
    """Cria um professor completo para testes."""
    from models.professor import Professor
    
    professor = Professor(
        id=usuario_professor.id,
        nome="Professor Teste",
        campus_id=campus_teste.id,
        especialidade="Matemática"
    )
    db_session.add(professor)
    db_session.commit()
    db_session.refresh(professor)
    return professor

@pytest.fixture
def gestor_completo(db_session, usuario_gestor, campus_teste):
    """Cria um gestor completo para testes."""
    from models.gestor import Gestor
    
    gestor = Gestor(
        id=usuario_gestor.id,
        nome="Gestor Teste",
        campus_id=campus_teste.id
    )
    db_session.add(gestor)
    db_session.commit()
    db_session.refresh(gestor)
    return gestor

@pytest.fixture
def client_com_auth(client, usuario_aluno, aluno_completo):
    """Cliente de teste com autenticação de aluno."""
    # Simular login criando cookie de sessão
    response = client.post(
        "/login",
        data={"email": usuario_aluno.email, "senha": "senha123"},
        follow_redirects=False
    )
    # O cookie de sessão será definido automaticamente pelo cliente
    return client

@pytest.fixture
def client_com_auth_professor(client, usuario_professor, professor_completo):
    """Cliente de teste com autenticação de professor."""
    response = client.post(
        "/login",
        data={"email": usuario_professor.email, "senha": "senha123"},
        follow_redirects=False
    )
    return client

@pytest.fixture
def client_com_auth_gestor(client, usuario_gestor, gestor_completo):
    """Cliente de teste com autenticação de gestor."""
    response = client.post(
        "/login",
        data={"email": usuario_gestor.email, "senha": "senha123"},
        follow_redirects=False
    )
    return client

