from sqlalchemy import Column, Integer, ForeignKey, Enum, Float
from dao.database import Base
from sqlalchemy.orm import relationship

class Resultado(Base):
    __tablename__ = 'resultados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aluno_id = Column(Integer, ForeignKey('alunos.idAluno'), nullable=False)
    prova_id = Column(Integer, ForeignKey('provas.id'), nullable=False)
    acertos = Column(Integer, nullable=False)
    situacao = Column(Enum('Insuficiente', 'Regular', 'Suficiente'), nullable=False)
    nota = Column(Float, nullable=False)
    total_questoes = Column(Integer, nullable=False)

    aluno = relationship("Aluno", back_populates="resultados")
    prova = relationship("Prova", back_populates="resultados")
