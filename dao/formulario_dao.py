from sqlalchemy.orm import Session
from models.formulario import Formulario
from models.pergunta_formulario import PerguntaFormulario
import json

class FormularioDAO:
    @staticmethod
    def create(db: Session, titulo: str, descricao: str):
        formulario = Formulario(
            titulo=titulo,
            descricao=descricao
        )
        db.add(formulario)
        db.commit()
        db.refresh(formulario)
        return formulario

    @staticmethod
    def get_by_id(db: Session, formulario_id: int):
        return db.query(Formulario).filter(Formulario.id == formulario_id).first()

    @staticmethod
    def get_all(db: Session):
        return db.query(Formulario).all()

    @staticmethod
    def get_active(db: Session):
        return db.query(Formulario).all()

    @staticmethod
    def add_pergunta(
        db: Session, 
        formulario_id: int, 
        tipo_pergunta: str, 
        enunciado: str, 
        opcoes: list = None
    ):
        pergunta = PerguntaFormulario(
            formulario_id=formulario_id,
            tipo_pergunta=tipo_pergunta,
            enunciado=enunciado,
            opcoes=json.dumps(opcoes) if opcoes else None
        )
        db.add(pergunta)
        db.commit()
        db.refresh(pergunta)
        return pergunta

    @staticmethod
    def get_perguntas(db: Session, formulario_id: int):
        return db.query(PerguntaFormulario).filter(
            PerguntaFormulario.formulario_id == formulario_id
        ).order_by(PerguntaFormulario.ordem).all()

    @staticmethod
    def delete(db: Session, formulario_id: int):
        formulario = db.query(Formulario).filter(Formulario.id == formulario_id).first()
        if formulario:
            db.delete(formulario)
            db.commit()
            print("Formulario deletado com sucesso")
            return True
        return False 