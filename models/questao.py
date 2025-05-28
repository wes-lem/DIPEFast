from sqlalchemy import Column, Integer, String, ForeignKey, Text
from dao.database import Base

class Questao(Base):
    __tablename__ = "questoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False)
    enunciado = Column(Text, nullable=False)
    imagem = Column(String, nullable=True)
    opcao_a = Column(String, nullable=False)
    opcao_b = Column(String, nullable=False)
    opcao_c = Column(String, nullable=False)
    opcao_d = Column(String, nullable=False)
    opcao_e = Column(String, nullable=False)
    resposta_correta = Column(String(1), nullable=False)

    # prova = relationship("Prova", back_populates="questoes")  # Ligação com a prova
    # respostas = relationship("Resposta", back_populates="questao")
