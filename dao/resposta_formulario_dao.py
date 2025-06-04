from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from models.resposta_formulario import RespostaFormulario
from models.aluno import Aluno
from models.formulario import Formulario
from models.pergunta_formulario import PerguntaFormulario

class RespostaFormularioDAO:
    @staticmethod
    def create_resposta(db: Session, aluno_id: int, formulario_id: int, pergunta_id: int, resposta_texto: str = None, resposta_opcoes: str = None):
        """Cria uma nova resposta de formulário para um aluno.
        Não comita aqui, o controller ou o serviço fará o commit da transação inteira.
        """
        nova_resposta = RespostaFormulario(
            aluno_id=aluno_id,
            formulario_id=formulario_id,
            pergunta_id=pergunta_id,
            resposta_texto=resposta_texto,
            resposta_opcoes=resposta_opcoes
        )
        db.add(nova_resposta)
        return nova_resposta

    @staticmethod
    def get_respostas_by_aluno_and_formulario(db: Session, aluno_id: int, formulario_id: int):
        """Retorna todas as respostas de um aluno para um formulário específico,
        juntamente com o enunciado da pergunta.
        """
        return db.query(
            RespostaFormulario,
            PerguntaFormulario.enunciado,
            PerguntaFormulario.tipo_pergunta,
            PerguntaFormulario.opcoes
        ).join(
            PerguntaFormulario, RespostaFormulario.pergunta_id == PerguntaFormulario.id
        ).filter(
            RespostaFormulario.aluno_id == aluno_id,
            RespostaFormulario.formulario_id == formulario_id
        ).all()

    @staticmethod
    def get_alunos_who_responded_formulario(db: Session, formulario_id: int):
        """Retorna a lista de alunos que responderam a um formulário específico."""
        return db.query(Aluno).join(
            RespostaFormulario, Aluno.idAluno == RespostaFormulario.aluno_id
        ).filter(
            RespostaFormulario.formulario_id == formulario_id
        ).distinct().all()

    @staticmethod
    def has_aluno_responded_formulario(db: Session, aluno_id: int, formulario_id: int):
        """Verifica se um aluno já respondeu a alguma parte de um formulário."""
        return db.query(RespostaFormulario).filter(
            RespostaFormulario.aluno_id == aluno_id,
            RespostaFormulario.formulario_id == formulario_id
        ).first() is not None

    @staticmethod
    def delete_respostas_from_formulario_by_aluno(db: Session, aluno_id: int, formulario_id: int):
        """Deleta todas as respostas de um aluno para um formulário específico."""
        db.query(RespostaFormulario).filter(
            RespostaFormulario.aluno_id == aluno_id,
            RespostaFormulario.formulario_id == formulario_id
        ).delete(synchronize_session=False)
        return True

    @staticmethod
    def get_total_respondedores_by_formulario(db: Session, formulario_id: int):
        """Retorna o número total de alunos que responderam a um formulário específico."""
        return db.query(func.count(func.distinct(RespostaFormulario.aluno_id))).filter(
            RespostaFormulario.formulario_id == formulario_id
        ).scalar() or 0

    @staticmethod
    def get_respostas_aluno(db: Session, aluno_id: int, formulario_id: int):
        return db.query(RespostaFormulario).filter(
            RespostaFormulario.aluno_id == aluno_id,
            RespostaFormulario.formulario_id == formulario_id
        ).all()

    @staticmethod
    def get_respostas_formulario(db: Session, formulario_id: int):
        return db.query(RespostaFormulario).filter(
            RespostaFormulario.formulario_id == formulario_id
        ).all()

    @staticmethod
    def get_estatisticas_formulario(db: Session, formulario_id: int):
        """Retorna estatísticas básicas sobre as respostas do formulário"""
        total_respostas = db.query(func.count(RespostaFormulario.id)).filter(
            RespostaFormulario.formulario_id == formulario_id
        ).scalar()
        
        total_alunos = db.query(func.count(func.distinct(RespostaFormulario.aluno_id))).filter(
            RespostaFormulario.formulario_id == formulario_id
        ).scalar()
        
        return {
            "total_respostas": total_respostas,
            "total_alunos": total_alunos
        } 