from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from dao.database import Base

class Formulario(Base):
    __tablename__ = "formularios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    # Campos para direcionamento
    turma_id = Column(Integer, ForeignKey('turmas.id'), nullable=True)  # Se None, não é direcionado a turma específica
    campus_id = Column(Integer, ForeignKey('campus.id'), nullable=True)  # Se None, não é direcionado a campus específico
    curso = Column(String(100), nullable=True)  # Se None, não é direcionado a curso específico (ex: "Redes de Computadores", "Agropecuária", "Partiu IF")
    data_criacao = Column(DateTime, server_default=func.now())
    
    perguntas = relationship("PerguntaFormulario", back_populates="formulario", cascade="all, delete-orphan") ## -> CORRIGIDO
    respostas = relationship("RespostaFormulario", back_populates="formulario", cascade="all, delete-orphan")
    turma = relationship("Turma", back_populates="formularios")
    campus = relationship("Campus", back_populates="formularios") 
