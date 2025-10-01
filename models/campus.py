from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from dao.database import Base

class Campus(Base):
    __tablename__ = 'campus'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    endereco = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    # Relacionamentos
    professores = relationship("Professor", back_populates="campus")
    turmas = relationship("Turma", back_populates="campus")
