"""
Testes para Data Access Objects (DAOs).
Verifica se os métodos de acesso a dados funcionam corretamente.
"""
import pytest

class TestFormularioDAO:
    """Testes para FormularioDAO."""
    
    def test_criar_formulario(self, db_session):
        """Testa criação de formulário via DAO."""
        from dao.formulario_dao import FormularioDAO
        
        formulario = FormularioDAO.create(
            db=db_session,
            titulo="Formulário Teste DAO",
            descricao="Descrição do teste",
            turma_id=None,
            campus_id=None,
            curso=None
        )
        
        assert formulario.id is not None
        assert formulario.titulo == "Formulário Teste DAO"
    
    def test_buscar_formulario_por_id(self, db_session):
        """Testa busca de formulário por ID."""
        from dao.formulario_dao import FormularioDAO
        
        formulario = FormularioDAO.create(
            db=db_session,
            titulo="Formulário para Buscar",
            descricao="Teste"
        )
        
        formulario_buscado = FormularioDAO.get_by_id(db_session, formulario.id)
        assert formulario_buscado is not None
        assert formulario_buscado.id == formulario.id
        assert formulario_buscado.titulo == "Formulário para Buscar"
    
    def test_get_for_aluno(self, db_session, aluno_completo):
        """Testa busca de formulários filtrados para aluno."""
        from dao.formulario_dao import FormularioDAO
        
        # Criar formulário sem filtro (para todos)
        formulario_geral = FormularioDAO.create(
            db=db_session,
            titulo="Formulário Geral",
            descricao="Para todos"
        )
        
        # Criar formulário direcionado ao curso do aluno
        formulario_curso = FormularioDAO.create(
            db=db_session,
            titulo="Formulário do Curso",
            descricao="Para o curso",
            curso=aluno_completo.curso
        )
        
        # Buscar formulários para o aluno
        formularios = FormularioDAO.get_for_aluno(db_session, aluno_completo.idAluno)
        
        # Deve incluir pelo menos o formulário geral e o do curso
        ids_formularios = [f.id for f in formularios]
        assert formulario_geral.id in ids_formularios
        assert formulario_curso.id in ids_formularios

class TestBancoQuestoesDAO:
    """Testes para BancoQuestoesDAO."""
    
    def test_criar_questao(self, db_session, professor_completo):
        """Testa criação de questão via DAO."""
        from dao.banco_questoes_dao import BancoQuestoesDAO
        
        questao = BancoQuestoesDAO.create(
            db=db_session,
            professor_id=professor_completo.id,
            enunciado="Teste de questão",
            opcao_a="A",
            opcao_b="B",
            opcao_c="C",
            opcao_d="D",
            opcao_e="E",
            resposta_correta="A",
            materia="Teste",
            publica=False
        )
        
        assert questao.id is not None
        assert questao.publica == False
    
    def test_buscar_questoes_publicas(self, db_session, professor_completo):
        """Testa busca de questões públicas."""
        from dao.banco_questoes_dao import BancoQuestoesDAO
        
        # Criar questão pública
        questao_publica = BancoQuestoesDAO.create(
            db=db_session,
            professor_id=professor_completo.id,
            enunciado="Questão Pública",
            opcao_a="A",
            opcao_b="B",
            opcao_c="C",
            opcao_d="D",
            opcao_e="E",
            resposta_correta="A",
            materia="Teste",
            publica=True
        )
        
        # Buscar questões públicas
        questoes_publicas = BancoQuestoesDAO.get_public_questoes(db_session)
        
        assert len(questoes_publicas) >= 1
        assert any(q.id == questao_publica.id for q in questoes_publicas)
    
    def test_get_available_for_professor(self, db_session, professor_completo):
        """Testa busca de questões disponíveis (próprias + públicas)."""
        from dao.banco_questoes_dao import BancoQuestoesDAO
        from models.usuario import Usuario
        from dao.senhaHash import criptografar_senha
        from models.professor import Professor
        from models.campus import Campus
        
        # Criar outro professor
        outro_usuario = Usuario(
            email="outro_prof@teste.com",
            senha_hash=criptografar_senha("senha"),
            tipo="professor"
        )
        db_session.add(outro_usuario)
        db_session.commit()
        
        outro_professor = Professor(
            id=outro_usuario.id,
            nome="Outro Professor",
            campus_id=professor_completo.campus_id
        )
        db_session.add(outro_professor)
        db_session.commit()
        
        # Criar questão própria
        questao_propria = BancoQuestoesDAO.create(
            db=db_session,
            professor_id=professor_completo.id,
            enunciado="Questão Própria",
            opcao_a="A",
            opcao_b="B",
            opcao_c="C",
            opcao_d="D",
            opcao_e="E",
            resposta_correta="A",
            materia="Teste",
            publica=False
        )
        
        # Criar questão pública de outro professor
        questao_publica_outro = BancoQuestoesDAO.create(
            db=db_session,
            professor_id=outro_professor.id,
            enunciado="Questão Pública de Outro",
            opcao_a="A",
            opcao_b="B",
            opcao_c="C",
            opcao_d="D",
            opcao_e="E",
            resposta_correta="A",
            materia="Teste",
            publica=True
        )
        
        # Buscar questões disponíveis para o professor
        questoes = BancoQuestoesDAO.get_available_for_professor(
            db_session, 
            professor_completo.id
        )
        
        ids_questoes = [q.id for q in questoes]
        assert questao_propria.id in ids_questoes
        assert questao_publica_outro.id in ids_questoes

