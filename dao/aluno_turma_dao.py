from sqlalchemy.orm import Session
from models.aluno_turma import AlunoTurma, StatusAlunoTurma
from models.turma import Turma, StatusTurma

class AlunoTurmaDAO:
    @staticmethod
    def create(db: Session, aluno_id: int, turma_id: int):
        """Adiciona um aluno a uma turma"""
        # Verificar se a turma existe e está ativa
        turma = db.query(Turma).filter(
            Turma.id == turma_id,
            Turma.status == StatusTurma.ATIVA
        ).first()
        
        if not turma:
            return None
        
        # Verificar se o aluno já está na turma
        existing = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.turma_id == turma_id
        ).first()
        
        if existing:
            # Se já existe mas está removido, reativar
            if existing.status == StatusAlunoTurma.REMOVIDO:
                existing.status = StatusAlunoTurma.ATIVO
                db.commit()
                db.refresh(existing)
                return existing
            else:
                # Já está ativo na turma
                return existing
        
        # Criar nova matrícula
        aluno_turma = AlunoTurma(
            aluno_id=aluno_id,
            turma_id=turma_id
        )
        db.add(aluno_turma)
        db.commit()
        db.refresh(aluno_turma)
        return aluno_turma

    @staticmethod
    def get_by_aluno_and_turma(db: Session, aluno_id: int, turma_id: int):
        """Busca matrícula específica de aluno em turma"""
        return db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.turma_id == turma_id
        ).first()

    @staticmethod
    def get_turmas_by_aluno(db: Session, aluno_id: int):
        """Busca todas as turmas de um aluno"""
        return db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).all()

    @staticmethod
    def get_alunos_by_turma(db: Session, turma_id: int):
        """Busca todos os alunos de uma turma"""
        return db.query(AlunoTurma).filter(
            AlunoTurma.turma_id == turma_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).all()

    @staticmethod
    def get_alunos_count_by_turma(db: Session, turma_id: int):
        """Conta quantos alunos estão em uma turma"""
        from sqlalchemy import func
        return db.query(func.count(AlunoTurma.id)).filter(
            AlunoTurma.turma_id == turma_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).scalar()

    @staticmethod
    def remove_aluno_from_turma(db: Session, aluno_id: int, turma_id: int):
        """Remove um aluno de uma turma (soft delete)"""
        aluno_turma = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.turma_id == turma_id
        ).first()
        
        if not aluno_turma:
            return False
        
        aluno_turma.status = StatusAlunoTurma.REMOVIDO
        db.commit()
        return True

    @staticmethod
    def hard_remove_aluno_from_turma(db: Session, aluno_id: int, turma_id: int):
        """Remove permanentemente um aluno de uma turma"""
        aluno_turma = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.turma_id == turma_id
        ).first()
        
        if not aluno_turma:
            return False
        
        db.delete(aluno_turma)
        db.commit()
        return True

    @staticmethod
    def is_aluno_in_turma(db: Session, aluno_id: int, turma_id: int):
        """Verifica se um aluno está ativo em uma turma"""
        aluno_turma = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.turma_id == turma_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).first()
        return aluno_turma is not None

    @staticmethod
    def get_turmas_with_details_by_aluno(db: Session, aluno_id: int):
        """Busca turmas de um aluno com detalhes"""
        return db.query(AlunoTurma).join(AlunoTurma.turma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).all()

    @staticmethod
    def get_alunos_with_details_by_turma(db: Session, turma_id: int):
        """Busca alunos de uma turma com detalhes"""
        return db.query(AlunoTurma).join(AlunoTurma.aluno).filter(
            AlunoTurma.turma_id == turma_id,
            AlunoTurma.status == StatusAlunoTurma.ATIVO
        ).all()

    @staticmethod
    def get_turmas_by_professor_with_alunos_count(db: Session, professor_id: int):
        """Busca turmas de um professor com contagem de alunos"""
        from sqlalchemy import func
        
        return db.query(
            Turma,
            func.count(AlunoTurma.id).label('total_alunos')
        ).outerjoin(
            AlunoTurma,
            (Turma.id == AlunoTurma.turma_id) & (AlunoTurma.status == StatusAlunoTurma.ATIVO)
        ).filter(
            Turma.professor_id == professor_id,
            Turma.status == StatusTurma.ATIVA
        ).group_by(Turma.id).all()
