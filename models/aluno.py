from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from dao.database import Base

class Aluno(Base):
    __tablename__ = "alunos"

    idAluno = Column(Integer, primary_key=True, index=True)
    idUser = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    ano = Column(Integer)
    curso = Column(String(100), nullable=False)
    imagem = Column(String(255), nullable=True)
    idade = Column(Integer, nullable=False)
    municipio = Column(String(100), nullable=False)
    zona = Column(String(20), nullable=False)  # "urbana" ou "rural"
    origem_escolar = Column(String(20), nullable=False)

    # NOVOS CAMPOS ADICIONADOS
    escola = Column(String(255), nullable=True)
    forma_ingresso = Column(String(50), nullable=True)
    acesso_internet = Column(Boolean, nullable=True)
    observacoes = Column(Text, nullable=True)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="aluno")
    respostas_formulario = relationship("RespostaFormulario", back_populates="aluno", cascade="all, delete-orphan")
    notificacoes = relationship("Notificacao", back_populates="aluno", cascade="all, delete-orphan")
    respostas = relationship("Resposta", back_populates="aluno", cascade="all, delete-orphan") ## -> ADICIONADO/CORRIGIDO
    resultados = relationship("Resultado", back_populates="aluno", cascade="all, delete-orphan")
