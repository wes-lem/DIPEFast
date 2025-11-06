from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base
import enum

class TipoNotificacaoProfessor(enum.Enum):
    PROVA_EXPIRADA = "prova_expirada"
    ALUNO_RESPONDEU = "aluno_respondeu"
    TURMA_CRIADA = "turma_criada"
    PROVA_CRIADA = "prova_criada"

class NotificacaoProfessor(Base):
    __tablename__ = 'notificacoes_professor'

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=False)
    tipo = Column(Enum(TipoNotificacaoProfessor), nullable=False)
    titulo = Column(String(255), nullable=False)
    mensagem = Column(String(500), nullable=False)
    data_criacao = Column(DateTime, server_default=func.current_timestamp())
    lida = Column(Boolean, default=False, nullable=False)

    # Relacionamentos
    professor = relationship("Professor", back_populates="notificacoes")
