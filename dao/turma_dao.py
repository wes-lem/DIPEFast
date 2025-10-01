import random
import string
from sqlalchemy.orm import Session
from models.turma import Turma, StatusTurma

class TurmaDAO:
    @staticmethod
    def generate_unique_code(db: Session, length: int = 6):
        """Gera um código único para a turma"""
        while True:
            # Gera código alfanumérico
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            
            # Verifica se já existe
            if not db.query(Turma).filter(Turma.codigo == code).first():
                return code

    @staticmethod
    def create(db: Session, nome: str, professor_id: int, campus_id: int):
        """Cria uma nova turma"""
        codigo = TurmaDAO.generate_unique_code(db)
        
        turma = Turma(
            nome=nome,
            codigo=codigo,
            professor_id=professor_id,
            campus_id=campus_id
        )
        db.add(turma)
        db.commit()
        db.refresh(turma)
        return turma

    @staticmethod
    def get_by_id(db: Session, turma_id: int):
        """Busca uma turma por ID"""
        return db.query(Turma).filter(Turma.id == turma_id).first()

    @staticmethod
    def get_by_codigo(db: Session, codigo: str):
        """Busca uma turma por código"""
        return db.query(Turma).filter(Turma.codigo == codigo).first()

    @staticmethod
    def get_by_professor(db: Session, professor_id: int):
        """Busca turmas por professor"""
        return db.query(Turma).filter(Turma.professor_id == professor_id).all()

    @staticmethod
    def get_active_by_professor(db: Session, professor_id: int):
        """Busca turmas ativas por professor"""
        return db.query(Turma).filter(
            Turma.professor_id == professor_id,
            Turma.status == StatusTurma.ATIVA
        ).all()

    @staticmethod
    def get_by_campus(db: Session, campus_id: int):
        """Busca turmas por campus"""
        return db.query(Turma).filter(Turma.campus_id == campus_id).all()

    @staticmethod
    def get_all(db: Session):
        """Busca todas as turmas"""
        return db.query(Turma).all()

    @staticmethod
    def get_all_with_details(db: Session):
        """Busca todas as turmas com dados relacionados carregados"""
        from sqlalchemy.orm import joinedload
        return db.query(Turma).options(
            joinedload(Turma.professor),
            joinedload(Turma.campus),
            joinedload(Turma.aluno_turmas)
        ).all()

    @staticmethod
    def update(db: Session, turma_id: int, nome: str = None, status: StatusTurma = None):
        """Atualiza uma turma"""
        turma = db.query(Turma).filter(Turma.id == turma_id).first()
        if not turma:
            return None
        
        if nome is not None:
            turma.nome = nome
        if status is not None:
            turma.status = status
            if status == StatusTurma.ARQUIVADA:
                from sqlalchemy.sql import func
                turma.data_arquivacao = func.current_timestamp()
        
        db.commit()
        db.refresh(turma)
        return turma

    @staticmethod
    def archive(db: Session, turma_id: int):
        """Arquiva uma turma"""
        return TurmaDAO.update(db, turma_id, status=StatusTurma.ARQUIVADA)

    @staticmethod
    def activate(db: Session, turma_id: int):
        """Reativa uma turma arquivada"""
        return TurmaDAO.update(db, turma_id, status=StatusTurma.ATIVA)

    @staticmethod
    def delete(db: Session, turma_id: int):
        """Remove uma turma permanentemente"""
        turma = db.query(Turma).filter(Turma.id == turma_id).first()
        if not turma:
            return False
        
        db.delete(turma)
        db.commit()
        return True

    @staticmethod
    def get_with_details(db: Session, turma_id: int):
        """Busca uma turma com detalhes do professor e campus"""
        from sqlalchemy.orm import joinedload
        return db.query(Turma).options(
            joinedload(Turma.professor),
            joinedload(Turma.campus),
            joinedload(Turma.aluno_turmas),
            joinedload(Turma.prova_turmas)
        ).filter(Turma.id == turma_id).first()

    @staticmethod
    def get_with_alunos_count(db: Session, professor_id: int):
        """Busca turmas do professor com contagem de alunos"""
        from sqlalchemy import func
        from models.aluno_turma import AlunoTurma, StatusAlunoTurma
        
        return db.query(
            Turma,
            func.count(AlunoTurma.id).label('total_alunos')
        ).outerjoin(
            AlunoTurma, 
            (Turma.id == AlunoTurma.turma_id) & (AlunoTurma.status == StatusAlunoTurma.ATIVO)
        ).filter(
            Turma.professor_id == professor_id
        ).group_by(Turma.id).all()

    @staticmethod
    def validate_code(db: Session, codigo: str):
        """Valida se um código de turma existe e está ativo"""
        turma = db.query(Turma).filter(
            Turma.codigo == codigo,
            Turma.status == StatusTurma.ATIVA
        ).first()
        return turma is not None
