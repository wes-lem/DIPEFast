from sqlalchemy import Column, Integer, String, ForeignKey
from dao.database import Base

class Gestor(Base):
    __tablename__ = 'gestores'

    id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    nome = Column(String(100), nullable=False)
    imagem = Column(String(255), nullable=True)  # Caminho para a foto de perfil 