from sqlalchemy.orm import Session
from models.pergunta_formulario import PerguntaFormulario

class PerguntaFormularioDAO:
    @staticmethod
    def create_pergunta(db: Session, formulario_id: int, tipo_pergunta: str, enunciado: str, opcoes: str = None):
        """Cria uma nova pergunta para um formulário."""
        nova_pergunta = PerguntaFormulario(
            formulario_id=formulario_id,
            tipo_pergunta=tipo_pergunta,
            enunciado=enunciado,
            opcoes=opcoes
        )
        db.add(nova_pergunta)
        db.flush()  # Para obter o ID da pergunta criada
        return nova_pergunta

    @staticmethod
    def get_by_formulario(db: Session, formulario_id: int):
        """Retorna todas as perguntas de um formulário específico."""
        return db.query(PerguntaFormulario).filter(
            PerguntaFormulario.formulario_id == formulario_id
        ).order_by(PerguntaFormulario.id).all()

    @staticmethod
    def get_by_id(db: Session, pergunta_id: int):
        """Retorna uma pergunta específica pelo ID."""
        return db.query(PerguntaFormulario).filter(
            PerguntaFormulario.id == pergunta_id
        ).first()

    @staticmethod
    def delete_by_formulario(db: Session, formulario_id: int):
        """Deleta todas as perguntas de um formulário específico."""
        db.query(PerguntaFormulario).filter(
            PerguntaFormulario.formulario_id == formulario_id
        ).delete(synchronize_session=False)
        return True

    @staticmethod
    def update_pergunta(db: Session, pergunta_id: int, tipo_pergunta: str = None, enunciado: str = None, opcoes: str = None):
        """Atualiza uma pergunta existente."""
        pergunta = db.query(PerguntaFormulario).filter(
            PerguntaFormulario.id == pergunta_id
        ).first()
        
        if not pergunta:
            return None
            
        if tipo_pergunta is not None:
            pergunta.tipo_pergunta = tipo_pergunta
        if enunciado is not None:
            pergunta.enunciado = enunciado
        if opcoes is not None:
            pergunta.opcoes = opcoes
            
        db.flush()
        return pergunta 