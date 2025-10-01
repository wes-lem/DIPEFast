from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dao.database import Base

class Professor(Base):
    __tablename__ = 'professores'

    id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    nome = Column(String(100), nullable=False)
    imagem = Column(String(255), nullable=True)  # Caminho para a foto de perfil
    especialidade = Column(String(100), nullable=True)
    campus_id = Column(Integer, ForeignKey('campus.id'), nullable=False)
    data_cadastro = Column(DateTime, server_default=func.current_timestamp())

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="professor")
    campus = relationship("Campus", back_populates="professores")
    turmas = relationship("Turma", back_populates="professor", cascade="all, delete-orphan")
    banco_questoes = relationship("BancoQuestoes", back_populates="professor", cascade="all, delete-orphan")
    provas = relationship("Prova", back_populates="professor", cascade="all, delete-orphan")
    prova_turmas = relationship("ProvaTurma", back_populates="professor", cascade="all, delete-orphan")
    notificacoes = relationship("NotificacaoProfessor", back_populates="professor", cascade="all, delete-orphan")
