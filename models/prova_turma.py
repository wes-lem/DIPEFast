from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base
import enum

class StatusProvaTurma(enum.Enum):
    ATIVA = "ativa"
    EXPIRADA = "expirada"
    ARQUIVADA = "arquivada"

class ProvaTurma(Base):
    __tablename__ = 'prova_turmas'

    id = Column(Integer, primary_key=True, index=True)
    prova_id = Column(Integer, ForeignKey('provas.id'), nullable=False)
    turma_id = Column(Integer, ForeignKey('turmas.id'), nullable=False)
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=False)
    data_inicio = Column(DateTime, nullable=False)
    data_expiracao = Column(DateTime, nullable=False)
    status = Column(Enum(StatusProvaTurma), default=StatusProvaTurma.ATIVA, nullable=False)
    data_criacao = Column(DateTime, server_default=func.current_timestamp())

    # Relacionamentos
    prova = relationship("Prova", back_populates="prova_turmas")
    turma = relationship("Turma", back_populates="prova_turmas")
    professor = relationship("Professor", back_populates="prova_turmas")
