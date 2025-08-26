from sqlalchemy import Column, Integer, String, ForeignKey, Text
from dao.database import Base
from sqlalchemy.orm import relationship

class Questao(Base):
    __tablename__ = "questoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False)
    enunciado = Column(Text, nullable=False)
    imagem = Column(String(255), nullable=True)
    opcao_a = Column(String(255), nullable=False)
    opcao_b = Column(String(255), nullable=False)
    opcao_c = Column(String(255), nullable=False)
    opcao_d = Column(String(255), nullable=False)
    opcao_e = Column(String(255), nullable=False)
    resposta_correta = Column(String(1), nullable=False)

    prova = relationship("Prova", back_populates="questoes") ## -> CORRIGIDO
    respostas = relationship("Resposta", back_populates="questao", cascade="all, delete-orphan") ## -> CORRIGIDO
