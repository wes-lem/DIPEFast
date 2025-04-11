from sqlalchemy import Column, Integer, String, ForeignKey
from dao.database import Base

class Resposta(Base):
    __tablename__ = "respostas"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.idAluno"), nullable=False)
    questao_id = Column(Integer, ForeignKey("questoes.id"), nullable=False)
    resposta_aluno = Column(String(1), nullable=False)  # Ex: 'a', 'b', 'c', 'd', 'e'
