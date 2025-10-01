from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from dao.database import Base

class ProvaQuestao(Base):
    __tablename__ = 'prova_questoes'

    id = Column(Integer, primary_key=True, index=True)
    prova_id = Column(Integer, ForeignKey('provas.id'), nullable=False)
    questao_banco_id = Column(Integer, ForeignKey('banco_questoes.id'), nullable=False)
    ordem = Column(Integer, nullable=False)  # Ordem da questão na prova

    # Relacionamentos
    prova = relationship("Prova", back_populates="prova_questoes")
    questao_banco = relationship("BancoQuestoes", back_populates="prova_questoes")
