from sqlalchemy.orm import Session
from models.prova_questao import ProvaQuestao

class ProvaQuestaoDAO:
    @staticmethod
    def create(db: Session, prova_id: int, questao_id: int, ordem: int):
        """Adiciona uma questão a uma prova"""
        prova_questao = ProvaQuestao(
            prova_id=prova_id,
            questao_banco_id=questao_id,
            ordem=ordem
        )
        db.add(prova_questao)
        db.commit()
        db.refresh(prova_questao)
        return prova_questao

    @staticmethod
    def get_by_prova(db: Session, prova_id: int):
        """Busca questões de uma prova ordenadas"""
        return db.query(ProvaQuestao).filter(
            ProvaQuestao.prova_id == prova_id
        ).order_by(ProvaQuestao.ordem).all()

    @staticmethod
    def get_by_prova_with_questao(db: Session, prova_id: int):
        """Busca questões de uma prova com detalhes da questão"""
        return db.query(ProvaQuestao).join(ProvaQuestao.questao_banco).filter(
            ProvaQuestao.prova_id == prova_id
        ).order_by(ProvaQuestao.ordem).all()

    @staticmethod
    def get_by_questao(db: Session, questao_id: int):
        """Busca provas que contêm uma questão específica"""
        return db.query(ProvaQuestao).filter(ProvaQuestao.questao_banco_id == questao_id).all()

    @staticmethod
    def remove_questao_from_prova(db: Session, prova_id: int, questao_id: int):
        """Remove uma questão de uma prova"""
        prova_questao = db.query(ProvaQuestao).filter(
            ProvaQuestao.prova_id == prova_id,
            ProvaQuestao.questao_banco_id == questao_id
        ).first()
        
        if not prova_questao:
            return False
        
        db.delete(prova_questao)
        db.commit()
        return True

    @staticmethod
    def remove_all_questoes_from_prova(db: Session, prova_id: int):
        """Remove todas as questões de uma prova"""
        db.query(ProvaQuestao).filter(ProvaQuestao.prova_id == prova_id).delete()
        db.commit()
        return True

    @staticmethod
    def update_ordem(db: Session, prova_id: int, questao_id: int, nova_ordem: int):
        """Atualiza a ordem de uma questão na prova"""
        prova_questao = db.query(ProvaQuestao).filter(
            ProvaQuestao.prova_id == prova_id,
            ProvaQuestao.questao_banco_id == questao_id
        ).first()
        
        if not prova_questao:
            return False
        
        prova_questao.ordem = nova_ordem
        db.commit()
        return True

    @staticmethod
    def reorder_questoes(db: Session, prova_id: int, questao_orders: list):
        """Reordena questões de uma prova"""
        for questao_id, nova_ordem in questao_orders:
            ProvaQuestaoDAO.update_ordem(db, prova_id, questao_id, nova_ordem)
        return True

    @staticmethod
    def get_count_by_prova(db: Session, prova_id: int):
        """Conta quantas questões uma prova tem"""
        from sqlalchemy import func
        return db.query(func.count(ProvaQuestao.id)).filter(
            ProvaQuestao.prova_id == prova_id
        ).scalar()

    @staticmethod
    def get_max_ordem_by_prova(db: Session, prova_id: int):
        """Busca a maior ordem de questão em uma prova"""
        from sqlalchemy import func
        return db.query(func.max(ProvaQuestao.ordem)).filter(
            ProvaQuestao.prova_id == prova_id
        ).scalar() or 0

    @staticmethod
    def add_questao_to_prova(db: Session, prova_id: int, questao_id: int):
        """Adiciona uma questão ao final de uma prova"""
        max_ordem = ProvaQuestaoDAO.get_max_ordem_by_prova(db, prova_id)
        return ProvaQuestaoDAO.create(db, prova_id, questao_id, max_ordem + 1)

    @staticmethod
    def is_questao_in_prova(db: Session, prova_id: int, questao_id: int):
        """Verifica se uma questão já está em uma prova"""
        prova_questao = db.query(ProvaQuestao).filter(
            ProvaQuestao.prova_id == prova_id,
            ProvaQuestao.questao_banco_id == questao_id
        ).first()
        return prova_questao is not None
