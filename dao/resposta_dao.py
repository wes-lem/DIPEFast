from sqlalchemy.orm import Session
from models.resposta import Resposta

class RespostaDAO:
    @staticmethod
    def create(db: Session, aluno_id: int, questao_id: int, resposta: str):
        nova_resposta = Resposta(
            aluno_id=aluno_id,
            questao_id=questao_id,
            resposta=resposta
        )
        db.add(nova_resposta)
        db.commit()
        db.refresh(nova_resposta)
        return nova_resposta
