from datetime import datetime
from sqlalchemy.orm import Session
from models.prova_turma import ProvaTurma, StatusProvaTurma

class ProvaTurmaDAO:
    @staticmethod
    def create(db: Session, prova_id: int, turma_id: int, professor_id: int, 
               data_inicio: datetime, data_expiracao: datetime):
        """Disponibiliza uma prova para uma turma"""
        prova_turma = ProvaTurma(
            prova_id=prova_id,
            turma_id=turma_id,
            professor_id=professor_id,
            data_inicio=data_inicio,
            data_expiracao=data_expiracao
        )
        db.add(prova_turma)
        db.commit()
        db.refresh(prova_turma)
        return prova_turma

    @staticmethod
    def get_by_id(db: Session, prova_turma_id: int):
        """Busca uma disponibilização de prova por ID"""
        return db.query(ProvaTurma).filter(ProvaTurma.id == prova_turma_id).first()

    @staticmethod
    def get_by_prova(db: Session, prova_id: int):
        """Busca turmas onde uma prova está disponibilizada"""
        return db.query(ProvaTurma).filter(ProvaTurma.prova_id == prova_id).all()

    @staticmethod
    def get_by_turma(db: Session, turma_id: int):
        """Busca provas disponibilizadas para uma turma"""
        return db.query(ProvaTurma).filter(ProvaTurma.turma_id == turma_id).all()

    @staticmethod
    def get_active_by_turma(db: Session, turma_id: int):
        """Busca provas ativas para uma turma"""
        return db.query(ProvaTurma).filter(
            ProvaTurma.turma_id == turma_id,
            ProvaTurma.status == StatusProvaTurma.ATIVA
        ).all()

    @staticmethod
    def get_by_professor(db: Session, professor_id: int):
        """Busca provas disponibilizadas por um professor"""
        return db.query(ProvaTurma).filter(ProvaTurma.professor_id == professor_id).all()

    @staticmethod
    def get_active_by_professor(db: Session, professor_id: int):
        """Busca provas ativas disponibilizadas por um professor"""
        return db.query(ProvaTurma).filter(
            ProvaTurma.professor_id == professor_id,
            ProvaTurma.status == StatusProvaTurma.ATIVA
        ).all()

    @staticmethod
    def get_expired_by_professor(db: Session, professor_id: int):
        """Busca provas expiradas de um professor"""
        return db.query(ProvaTurma).filter(
            ProvaTurma.professor_id == professor_id,
            ProvaTurma.status == StatusProvaTurma.EXPIRADA
        ).all()

    @staticmethod
    def update_status(db: Session, prova_turma_id: int, status: StatusProvaTurma):
        """Atualiza o status de uma disponibilização de prova"""
        prova_turma = db.query(ProvaTurma).filter(ProvaTurma.id == prova_turma_id).first()
        if not prova_turma:
            return False
        
        prova_turma.status = status
        db.commit()
        return True

    @staticmethod
    def extend_deadline(db: Session, prova_turma_id: int, nova_data_expiracao: datetime):
        """Estende o prazo de uma prova"""
        prova_turma = db.query(ProvaTurma).filter(ProvaTurma.id == prova_turma_id).first()
        if not prova_turma:
            return False
        
        prova_turma.data_expiracao = nova_data_expiracao
        if prova_turma.status == StatusProvaTurma.EXPIRADA:
            prova_turma.status = StatusProvaTurma.ATIVA
        
        db.commit()
        return True

    @staticmethod
    def archive(db: Session, prova_turma_id: int):
        """Arquiva uma disponibilização de prova"""
        return ProvaTurmaDAO.update_status(db, prova_turma_id, StatusProvaTurma.ARQUIVADA)

    @staticmethod
    def delete(db: Session, prova_turma_id: int):
        """Remove uma disponibilização de prova"""
        prova_turma = db.query(ProvaTurma).filter(ProvaTurma.id == prova_turma_id).first()
        if not prova_turma:
            return False
        
        db.delete(prova_turma)
        db.commit()
        return True

    @staticmethod
    def check_and_update_expired(db: Session):
        """Verifica e atualiza provas expiradas"""
        now = datetime.now()
        expired_provas = db.query(ProvaTurma).filter(
            ProvaTurma.data_expiracao < now,
            ProvaTurma.status == StatusProvaTurma.ATIVA
        ).all()
        
        for prova_turma in expired_provas:
            prova_turma.status = StatusProvaTurma.EXPIRADA
        
        db.commit()
        return len(expired_provas)

    @staticmethod
    def get_provas_for_aluno(db: Session, aluno_id: int):
        """Busca provas disponíveis para um aluno (baseado nas suas turmas)"""
        from models.aluno_turma import AlunoTurma, StatusAlunoTurma
        
        # Busca turmas do aluno
        turmas_aluno = db.query(AlunoTurma.turma_id).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).subquery()
        
        # Busca provas ativas dessas turmas
        return db.query(ProvaTurma).filter(
            ProvaTurma.turma_id.in_(turmas_aluno),
            ProvaTurma.status == StatusProvaTurma.ATIVA
        ).all()

    @staticmethod
    def get_provas_expired_for_aluno(db: Session, aluno_id: int):
        """Busca provas expiradas para um aluno (para consulta)"""
        from models.aluno_turma import AlunoTurma, StatusAlunoTurma
        
        # Busca turmas do aluno
        turmas_aluno = db.query(AlunoTurma.turma_id).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).subquery()
        
        # Busca provas expiradas dessas turmas
        return db.query(ProvaTurma).filter(
            ProvaTurma.turma_id.in_(turmas_aluno),
            ProvaTurma.status == StatusProvaTurma.EXPIRADA
        ).all()

    @staticmethod
    def get_with_details(db: Session, prova_turma_id: int):
        """Busca disponibilização de prova com detalhes"""
        return db.query(ProvaTurma).join(ProvaTurma.prova).join(ProvaTurma.turma).filter(
            ProvaTurma.id == prova_turma_id
        ).first()
