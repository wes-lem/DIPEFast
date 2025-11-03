from sqlalchemy.orm import Session
from models.banco_questoes import BancoQuestoes, StatusQuestao

class BancoQuestoesDAO:
    @staticmethod
    def create(db: Session, professor_id: int, enunciado: str, opcao_a: str, opcao_b: str, 
               opcao_c: str, opcao_d: str, opcao_e: str, resposta_correta: str, 
               materia: str, imagem: str = None, publica: bool = False):
        """Cria uma nova questão no banco"""
        questao = BancoQuestoes(
            professor_id=professor_id,
            enunciado=enunciado,
            opcao_a=opcao_a,
            opcao_b=opcao_b,
            opcao_c=opcao_c,
            opcao_d=opcao_d,
            opcao_e=opcao_e,
            resposta_correta=resposta_correta,
            materia=materia,
            imagem=imagem,
            publica=publica
        )
        db.add(questao)
        db.commit()
        db.refresh(questao)
        return questao

    @staticmethod
    def get_by_id(db: Session, questao_id: int):
        """Busca uma questão por ID"""
        return db.query(BancoQuestoes).filter(BancoQuestoes.id == questao_id).first()

    @staticmethod
    def get_by_professor(db: Session, professor_id: int):
        """Busca questões por professor"""
        return db.query(BancoQuestoes).filter(BancoQuestoes.professor_id == professor_id).all()

    @staticmethod
    def get_active_by_professor(db: Session, professor_id: int):
        """Busca questões ativas por professor"""
        return db.query(BancoQuestoes).filter(
            BancoQuestoes.professor_id == professor_id,
            BancoQuestoes.status == StatusQuestao.ATIVA
        ).all()
    
    @staticmethod
    def get_available_for_professor(db: Session, professor_id: int, materia: str = None):
        """Busca questões disponíveis para um professor (suas próprias + públicas de outros)"""
        from sqlalchemy import or_
        query = db.query(BancoQuestoes).filter(
            BancoQuestoes.status == StatusQuestao.ATIVA,
            or_(
                BancoQuestoes.professor_id == professor_id,
                BancoQuestoes.publica == True
            )
        )
        if materia:
            query = query.filter(BancoQuestoes.materia == materia)
        return query.all()
    
    @staticmethod
    def get_public_questoes(db: Session, materia: str = None):
        """Busca questões públicas de todos os professores"""
        query = db.query(BancoQuestoes).filter(
            BancoQuestoes.status == StatusQuestao.ATIVA,
            BancoQuestoes.publica == True
        )
        if materia:
            query = query.filter(BancoQuestoes.materia == materia)
        return query.all()

    @staticmethod
    def get_by_materia(db: Session, materia: str):
        """Busca questões por matéria"""
        return db.query(BancoQuestoes).filter(
            BancoQuestoes.materia == materia,
            BancoQuestoes.status == StatusQuestao.ATIVA
        ).all()

    @staticmethod
    def get_by_professor_and_materia(db: Session, professor_id: int, materia: str):
        """Busca questões por professor e matéria"""
        return db.query(BancoQuestoes).filter(
            BancoQuestoes.professor_id == professor_id,
            BancoQuestoes.materia == materia,
            BancoQuestoes.status == StatusQuestao.ATIVA
        ).all()

    @staticmethod
    def get_all(db: Session):
        """Busca todas as questões ativas"""
        return db.query(BancoQuestoes).filter(BancoQuestoes.status == StatusQuestao.ATIVA).all()

    @staticmethod
    def update(db: Session, questao_id: int, enunciado: str = None, opcao_a: str = None,
               opcao_b: str = None, opcao_c: str = None, opcao_d: str = None,
               opcao_e: str = None, resposta_correta: str = None, materia: str = None,
               imagem: str = None):
        """Atualiza uma questão"""
        questao = db.query(BancoQuestoes).filter(BancoQuestoes.id == questao_id).first()
        if not questao:
            return None
        
        if enunciado is not None:
            questao.enunciado = enunciado
        if opcao_a is not None:
            questao.opcao_a = opcao_a
        if opcao_b is not None:
            questao.opcao_b = opcao_b
        if opcao_c is not None:
            questao.opcao_c = opcao_c
        if opcao_d is not None:
            questao.opcao_d = opcao_d
        if opcao_e is not None:
            questao.opcao_e = opcao_e
        if resposta_correta is not None:
            questao.resposta_correta = resposta_correta
        if materia is not None:
            questao.materia = materia
        if imagem is not None:
            questao.imagem = imagem
        
        db.commit()
        db.refresh(questao)
        return questao

    @staticmethod
    def archive(db: Session, questao_id: int):
        """Arquiva uma questão"""
        questao = db.query(BancoQuestoes).filter(BancoQuestoes.id == questao_id).first()
        if not questao:
            return False
        
        questao.status = StatusQuestao.ARQUIVADA
        db.commit()
        return True

    @staticmethod
    def activate(db: Session, questao_id: int):
        """Reativa uma questão arquivada"""
        questao = db.query(BancoQuestoes).filter(BancoQuestoes.id == questao_id).first()
        if not questao:
            return False
        
        questao.status = StatusQuestao.ATIVA
        db.commit()
        return True

    @staticmethod
    def delete(db: Session, questao_id: int):
        """Remove uma questão permanentemente"""
        questao = db.query(BancoQuestoes).filter(BancoQuestoes.id == questao_id).first()
        if not questao:
            return False
        
        db.delete(questao)
        db.commit()
        return True

    @staticmethod
    def get_materias_by_professor(db: Session, professor_id: int):
        """Busca matérias únicas de um professor"""
        from sqlalchemy import distinct
        return db.query(distinct(BancoQuestoes.materia)).filter(
            BancoQuestoes.professor_id == professor_id,
            BancoQuestoes.status == StatusQuestao.ATIVA
        ).all()

    @staticmethod
    def get_count_by_professor(db: Session, professor_id: int):
        """Conta questões de um professor"""
        from sqlalchemy import func
        return db.query(func.count(BancoQuestoes.id)).filter(
            BancoQuestoes.professor_id == professor_id,
            BancoQuestoes.status == StatusQuestao.ATIVA
        ).scalar()

    @staticmethod
    def search_questoes(db: Session, professor_id: int, search_term: str = None, materia: str = None):
        """Busca questões com filtros"""
        query = db.query(BancoQuestoes).filter(
            BancoQuestoes.professor_id == professor_id,
            BancoQuestoes.status == StatusQuestao.ATIVA
        )
        
        if search_term:
            query = query.filter(BancoQuestoes.enunciado.ilike(f"%{search_term}%"))
        
        if materia:
            query = query.filter(BancoQuestoes.materia == materia)
        
        return query.all()
