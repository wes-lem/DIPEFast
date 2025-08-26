from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from dao.database import Base

class Formulario(Base):
    __tablename__ = "formularios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, server_default=func.now())
    
    perguntas = relationship("PerguntaFormulario", back_populates="formulario", cascade="all, delete-orphan") ## -> CORRIGIDO
    respostas = relationship("RespostaFormulario", back_populates="formulario", cascade="all, delete-orphan") 
