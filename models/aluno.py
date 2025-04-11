from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.resposta import Resposta
from dao.database import Base

class Aluno(Base):
    __tablename__ = "alunos"

    idAluno = Column(Integer, primary_key=True, index=True)
    idUser = Column(Integer, nullable=False)
    nome = Column(String)
    ano = Column(Integer)
    curso = Column(String)
    imagem = Column(String, nullable=True)
    idade = Column(Integer, nullable=False)
    municipio = Column(String(100), nullable=False)
    zona = Column(String(20), nullable=False)  # "urbana" ou "rural"
    origem_escolar = Column(String(20), nullable=False)

    # respostas = relationship("Resposta", backref="respostas", lazy="subquery")

