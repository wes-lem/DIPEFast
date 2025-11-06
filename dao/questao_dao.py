from sqlalchemy.orm import Session
from models.questao import Questao

class QuestaoDAO:
    @staticmethod
    def get_all(db: Session):
        """ Retorna todas as questões cadastradas. """
        return db.query(Questao).all()

    @staticmethod
    def get_by_id(db: Session, questao_id: int):
        """ Retorna uma questão específica pelo ID. """
        return db.query(Questao).filter(Questao.id == questao_id).first()

    @staticmethod
    def get_by_prova(db: Session, prova_id: int):
        """ Retorna todas as questões de uma prova específica. """
        return db.query(Questao).filter(Questao.prova_id == prova_id).all()

    @staticmethod
    def create(db: Session, prova_id: int, enunciado: str, imagem: str = None, alternativa_correta: str = "a"):
        """ Cria uma nova questão para uma prova. """
        nova_questao = Questao(
            prova_id=prova_id,
            enunciado=enunciado,
            imagem=imagem,
            alternativa_correta=alternativa_correta
        )
        db.add(nova_questao)
        db.commit()
        db.refresh(nova_questao)
        return nova_questao

    @staticmethod
    def delete(db: Session, questao_id: int):
        """ Remove uma questão pelo ID. """
        questao = db.query(Questao).filter(Questao.id == questao_id).first()
        if questao:
            db.delete(questao)
            db.commit()
            return True
        return False
