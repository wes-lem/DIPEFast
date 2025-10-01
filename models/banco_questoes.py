from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base
import enum

class StatusQuestao(enum.Enum):
    ATIVA = "ativa"
    ARQUIVADA = "arquivada"

class BancoQuestoes(Base):
    __tablename__ = 'banco_questoes'

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey('professores.id'), nullable=False)
    enunciado = Column(Text, nullable=False)
    imagem = Column(String(255), nullable=True)  # Caminho para imagem da questão
    opcao_a = Column(String(500), nullable=False)
    opcao_b = Column(String(500), nullable=False)
    opcao_c = Column(String(500), nullable=False)
    opcao_d = Column(String(500), nullable=False)
    opcao_e = Column(String(500), nullable=False)
    resposta_correta = Column(String(1), nullable=False)  # A, B, C, D ou E
    materia = Column(String(100), nullable=False)
    status = Column(Enum(StatusQuestao), default=StatusQuestao.ATIVA, nullable=False)
    data_criacao = Column(DateTime, server_default=func.current_timestamp())

    # Relacionamentos
    professor = relationship("Professor", back_populates="banco_questoes")
    prova_questoes = relationship("ProvaQuestao", back_populates="questao_banco", cascade="all, delete-orphan")
