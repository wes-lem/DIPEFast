from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from dao.database import Base

class PerguntaFormulario(Base):
    __tablename__ = "perguntas_formulario"

    id = Column(Integer, primary_key=True, index=True)
    formulario_id = Column(Integer, ForeignKey("formularios.id"), nullable=False)
    tipo_pergunta = Column(String(50), nullable=False)  # texto, escolha_unica, multipla_escolha
    enunciado = Column(Text, nullable=False)
    opcoes = Column(Text, nullable=True)  # JSON string para opções de escolha
    
    # Relacionamentos
    # formulario = relationship("Formulario", back_populates="perguntas")
    # respostas = relationship("RespostaFormulario", back_populates="pergunta") 