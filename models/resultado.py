from sqlalchemy import Column, Integer, String, ForeignKey, Float
from dao.database import Base
from sqlalchemy.orm import relationship

class Resultado(Base):
    __tablename__ = 'resultados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aluno_id = Column(Integer, ForeignKey('alunos.idAluno'), nullable=False)
    prova_id = Column(Integer, ForeignKey('provas.id'), nullable=False)
    nota = Column(Float, nullable=False)
    acertos = Column(Integer, nullable=False)
    total_questoes = Column(Integer, nullable=False)
    situacao = Column(String(50), nullable=False, default="aprovado")

    aluno = relationship("Aluno", back_populates="resultados")
    prova = relationship("Prova", back_populates="resultados")
