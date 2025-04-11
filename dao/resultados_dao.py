# dao/resultados_dao.py

from sqlalchemy.orm import Session
from models.resultado import Resultado

class ResultadoDAO:
    @staticmethod
    def criar_resultado(db: Session, aluno_id: int, prova_id: int, acertos: int, situacao: str):
        novo_resultado = Resultado(
            aluno_id=aluno_id,
            prova_id=prova_id,
            acertos=acertos,
            situacao=situacao
        )
        db.add(novo_resultado)
        db.commit()
        db.refresh(novo_resultado)
        return novo_resultado

    @staticmethod
    def buscar_por_aluno_e_prova(db: Session, aluno_id: int, prova_id: int):
        return db.query(Resultado).filter_by(aluno_id=aluno_id, prova_id=prova_id).first()
