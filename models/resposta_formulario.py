from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from dao.database import Base

class RespostaFormulario(Base):
    __tablename__ = "respostas_formulario"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.idAluno"), nullable=False)
    formulario_id = Column(Integer, ForeignKey("formularios.id"), nullable=False)
    pergunta_id = Column(Integer, ForeignKey("perguntas_formulario.id"), nullable=False)
    resposta_texto = Column(Text, nullable=True)
    resposta_opcoes = Column(Text, nullable=True)  # JSON string para respostas de múltipla escolha
    data_resposta = Column(DateTime, server_default=func.now())
    
    aluno = relationship("Aluno", back_populates="respostas_formulario") ## -> CORRIGIDO
    formulario = relationship("Formulario", back_populates="respostas") ## -> CORRIGIDO
    pergunta = relationship("PerguntaFormulario", back_populates="respostas")
