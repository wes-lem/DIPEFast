from sqlalchemy import Column, Integer, String, ForeignKey
from dao.database import Base
from sqlalchemy.orm import relationship

class Resposta(Base):
    __tablename__ = "respostas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.idAluno"), nullable=False)
    questao_id = Column(Integer, ForeignKey("banco_questoes.id"), nullable=False)
    resposta = Column(String(1), nullable=False)  # Ex: 'A', 'B', 'C', 'D', 'E'

    aluno = relationship("Aluno", back_populates="respostas")
