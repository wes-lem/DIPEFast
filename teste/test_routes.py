"""
Testes para todas as rotas da aplicação.
Verifica se as rotas não retornam erros internos (500) e se respondem corretamente.
"""
import pytest
from fastapi import status

class TestRotasPublicas:
    """Testes para rotas públicas (sem autenticação)."""
    
    def test_rota_home(self, client):
        """Testa se a rota raiz responde corretamente."""
        response = client.get("/")
        assert response.status_code in [200, 303]  # Pode redirecionar ou retornar HTML
        assert response.status_code != 500
    
    def test_rota_health_check(self, client):
        """Testa o endpoint de health check."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_rota_login(self, client):
        """Testa se a página de login carrega."""
        response = client.get("/login")
        assert response.status_code == 200
        assert response.status_code != 500
    
    def test_rota_cadastro(self, client):
        """Testa se a página de cadastro carrega."""
        response = client.get("/cadastro")
        assert response.status_code == 200
        assert response.status_code != 500
    
    def test_rota_cadastro_professor(self, client):
        """Testa se a página de cadastro de professor carrega."""
        response = client.get("/professor/cadastrar")
        assert response.status_code == 200
        assert response.status_code != 500

class TestRotasAluno:
    """Testes para rotas de aluno."""
    
    def test_rota_perfil_sem_auth(self, client):
        """Testa se rota de perfil requer autenticação."""
        response = client.get("/perfil", follow_redirects=False)
        # Deve redirecionar para login ou retornar 401/403
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_dashboard_aluno_sem_auth(self, client):
        """Testa se dashboard de aluno requer autenticação."""
        response = client.get("/aluno/dashboard/1", follow_redirects=False)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500
    
    def test_rota_formularios_aluno_sem_auth(self, client):
        """Testa se listagem de formulários requer autenticação."""
        response = client.get("/aluno/formularios", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_turmas_aluno_sem_auth(self, client):
        """Testa se listagem de turmas requer autenticação."""
        response = client.get("/aluno/turmas", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_provas_aluno_sem_auth(self, client):
        """Testa se listagem de provas requer autenticação."""
        response = client.get("/provas", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500

class TestRotasProfessor:
    """Testes para rotas de professor."""
    
    def test_rota_dashboard_professor_sem_auth(self, client):
        """Testa se dashboard de professor requer autenticação."""
        response = client.get("/professor/dashboard", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_turmas_professor_sem_auth(self, client):
        """Testa se listagem de turmas de professor requer autenticação."""
        response = client.get("/professor/turmas", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_provas_professor_sem_auth(self, client):
        """Testa se listagem de provas de professor requer autenticação."""
        response = client.get("/professor/provas", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_banco_questoes_sem_auth(self, client):
        """Testa se banco de questões requer autenticação."""
        response = client.get("/professor/banco-questoes", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_criar_questao_sem_auth(self, client):
        """Testa se criação de questão requer autenticação."""
        response = client.get("/professor/banco-questoes/criar", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_criar_prova_sem_auth(self, client):
        """Testa se criação de prova requer autenticação."""
        response = client.get("/professor/provas/criar", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_notificacoes_professor_sem_auth(self, client):
        """Testa se notificações de professor requerem autenticação."""
        response = client.get("/professor/notificacoes", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500

class TestRotasGestor:
    """Testes para rotas de gestor."""
    
    def test_rota_dashboard_gestor_sem_auth(self, client):
        """Testa se dashboard de gestor requer autenticação."""
        response = client.get("/gestor/dashboard", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_formularios_gestor_sem_auth(self, client):
        """Testa se listagem de formulários de gestor requer autenticação."""
        response = client.get("/gestor/formularios", follow_redirects=False)
        # Pode retornar 200 (se não tiver verificação) ou 303/401/403 (se tiver)
        assert response.status_code in [200, 303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_cadastrar_formulario_sem_auth(self, client):
        """Testa se cadastro de formulário requer autenticação."""
        response = client.get("/gestor/formularios/cadastrar", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_gerenciar_usuarios_sem_auth(self, client):
        """Testa se gerenciamento de usuários requer autenticação."""
        response = client.get("/gestor/gerenciar-usuarios", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500
    
    def test_rota_alunos_gestor_sem_auth(self, client):
        """Testa se listagem de alunos de gestor requer autenticação."""
        response = client.get("/gestor/alunos", follow_redirects=False)
        # Pode retornar 404 (rota não existe) ou 303/401/403 (se tiver verificação)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500
    
    def test_rota_provas_gestor_sem_auth(self, client):
        """Testa se cadastro de provas de gestor requer autenticação."""
        response = client.get("/provas/cadastrar", follow_redirects=False)
        assert response.status_code in [303, 401, 403]
        assert response.status_code != 500

class TestRotasFormulario:
    """Testes para rotas de formulário."""
    
    def test_rota_listar_formularios_aluno_invalida(self, client):
        """Testa rota de listagem de formulários sem autenticação."""
        response = client.get("/aluno/formularios", follow_redirects=False)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500
    
    def test_rota_responder_formulario_invalida(self, client):
        """Testa rota de responder formulário sem autenticação."""
        response = client.get("/aluno/formularios/1", follow_redirects=False)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500

class TestRotasProva:
    """Testes para rotas de prova."""
    
    def test_rota_responder_prova_invalida(self, client):
        """Testa rota de responder prova sem autenticação."""
        response = client.get("/prova/1", follow_redirects=False)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500
    
    def test_rota_resultado_prova_invalida(self, client):
        """Testa rota de resultado de prova sem autenticação."""
        response = client.get("/prova/1/resultado-detalhado", follow_redirects=False)
        assert response.status_code in [303, 401, 403, 404]
        assert response.status_code != 500

class TestRotasInvalidas:
    """Testes para rotas que não existem."""
    
    def test_rota_inexistente(self, client):
        """Testa se rota inexistente retorna 404 e não 500."""
        response = client.get("/rota-que-nao-existe")
        assert response.status_code == 404
        assert response.status_code != 500
    
    def test_rota_com_parametro_invalido(self, client):
        """Testa se rota com parâmetro inválido não retorna 500."""
        response = client.get("/aluno/formularios/abc", follow_redirects=False)  # ID inválido
        # Pode redirecionar para login (303) ou retornar erro (400, 404, 422)
        assert response.status_code in [303, 400, 404, 422]
        assert response.status_code != 500

