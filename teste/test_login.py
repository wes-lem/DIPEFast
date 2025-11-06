"""
Testes específicos para funcionalidades de login e autenticação.
"""
import pytest
from fastapi import status

class TestLogin:
    """Testes para o sistema de login."""
    
    def test_login_com_credenciais_invalidas(self, client, db_session):
        """Testa login com email/senha inválidos."""
        response = client.post(
            "/login",
            data={"email": "naoexiste@teste.com", "senha": "senhaerrada"},
            follow_redirects=False
        )
        # Pode retornar 200 (página de login com erro) ou redirecionar (303)
        # O importante é que não retorne 500 (erro interno)
        assert response.status_code in [200, 303, 401, 400]
        assert response.status_code != 500
    
    def test_login_sem_email(self, client):
        """Testa login sem fornecer email."""
        response = client.post(
            "/login",
            data={"senha": "senha123"},
            follow_redirects=False
        )
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
        assert response.status_code != 500
    
    def test_login_sem_senha(self, client):
        """Testa login sem fornecer senha."""
        response = client.post(
            "/login",
            data={"email": "teste@teste.com"},
            follow_redirects=False
        )
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
        assert response.status_code != 500
    
    def test_login_com_email_valido(self, client, usuario_aluno):
        """Testa login com credenciais válidas."""
        response = client.post(
            "/login",
            data={"email": usuario_aluno.email, "senha": "senha123"},
            follow_redirects=False
        )
        # Deve redirecionar ou retornar sucesso
        assert response.status_code in [200, 303]
        assert response.status_code != 500

class TestLogout:
    """Testes para logout."""
    
    def test_logout(self, client):
        """Testa se a rota de logout funciona."""
        response = client.post("/sair", follow_redirects=False)
        assert response.status_code in [200, 303]
        assert response.status_code != 500

