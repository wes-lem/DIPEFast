from sqlalchemy import Column, Integer, String, ForeignKey
from dao.database import Base

class Resultado(Base):
    __tablename__ = 'resultados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aluno_id = Column(Integer, ForeignKey('alunos.idAluno'), nullable=False)
    prova_id = Column(Integer, ForeignKey('provas.id'), nullable=False)
    acertos = Column(Integer, nullable=False)
    situacao = Column(String(50), nullable=False)