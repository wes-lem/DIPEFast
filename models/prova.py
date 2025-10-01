from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import relationship
from dao.database import Base
import enum

class StatusProva(enum.Enum):
    RASCUNHO = "rascunho"
    ATIVA = "ativa"
    EXPIRADA = "expirada"
    ARQUIVADA = "arquivada"

class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    materia = Column(String(100), nullable=False)
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=False)
    status = Column(Enum(StatusProva), default=StatusProva.RASCUNHO, nullable=False)
    data_criacao = Column(TIMESTAMP, server_default=func.current_timestamp())
    data_atualizacao = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relacionamentos
    professor = relationship("Professor", back_populates="provas")
    questoes = relationship("Questao", back_populates="prova", cascade="all, delete-orphan") ## -> ADICIONADO/CORRIGIDO
    resultados = relationship("Resultado", back_populates="prova", cascade="all, delete-orphan")
    prova_questoes = relationship("ProvaQuestao", back_populates="prova", cascade="all, delete-orphan")
    prova_turmas = relationship("ProvaTurma", back_populates="prova", cascade="all, delete-orphan")
