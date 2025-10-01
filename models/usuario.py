from sqlalchemy import Column, Integer, String
from dao.database import Base
from sqlalchemy.orm import relationship

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)  # Aluno, Gestor, Professor

    aluno = relationship("Aluno", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    gestor = relationship("Gestor", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    professor = relationship("Professor", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
