from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from dao.database import Base

class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.idAluno"), nullable=False)
    titulo = Column(String(255), nullable=False)
    mensagem = Column(Text, nullable=True)
    link = Column(String(255), nullable=True)  # Link para o formulário ou outra página
    lida = Column(Boolean, default=False)
    data_criacao = Column(DateTime, server_default=func.now())
    
    # Relacionamentos
    aluno = relationship("Aluno", back_populates="notificacoes") ## -> CORRIGIDO
