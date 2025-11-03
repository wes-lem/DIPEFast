from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base
import enum

class StatusTurma(enum.Enum):
    ATIVA = "ativa"
    ARQUIVADA = "arquivada"
    EXCLUIDA = "excluida"

class Turma(Base):
    __tablename__ = 'turmas'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    codigo = Column(String(6), unique=True, nullable=False)  # Código alfanumérico de 6 caracteres
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=False)
    campus_id = Column(Integer, ForeignKey('campus.id'), nullable=False)
    status = Column(Enum(StatusTurma), default=StatusTurma.ATIVA, nullable=False)
    data_criacao = Column(DateTime, server_default=func.current_timestamp())
    data_arquivacao = Column(DateTime, nullable=True)

    # Relacionamentos
    professor = relationship("Professor", back_populates="turmas")
    campus = relationship("Campus", back_populates="turmas")
    aluno_turmas = relationship("AlunoTurma", back_populates="turma", cascade="all, delete-orphan")
    prova_turmas = relationship("ProvaTurma", back_populates="turma", cascade="all, delete-orphan")
    formularios = relationship("Formulario", back_populates="turma")
