from sqlalchemy import Column, Integer, String
from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import relationship

from dao.database import Base

class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    materia = Column(String(100), nullable=False) 
    data_criacao = Column(TIMESTAMP, server_default=func.current_timestamp())

    questoes = relationship("Questao", back_populates="prova", cascade="all, delete-orphan") ## -> ADICIONADO/CORRIGIDO
    resultados = relationship("Resultado", back_populates="prova", cascade="all, delete-orphan")
