from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base
import enum

class StatusAlunoTurma(enum.Enum):
    ATIVO = "ativo"
    REMOVIDO = "removido"

class AlunoTurma(Base):
    __tablename__ = 'aluno_turmas'

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey('alunos.idAluno'), nullable=False)
    turma_id = Column(Integer, ForeignKey('turmas.id'), nullable=False)
    data_entrada = Column(DateTime, server_default=func.current_timestamp())
    status = Column(Enum(StatusAlunoTurma), default=StatusAlunoTurma.ATIVO, nullable=False)

    # Relacionamentos
    aluno = relationship("Aluno", back_populates="aluno_turmas")
    turma = relationship("Turma", back_populates="aluno_turmas")
