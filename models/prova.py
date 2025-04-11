from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from dao.database import engine  # Importe o engine
from sqlalchemy import TIMESTAMP, func

from dao.database import Base

class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    materia = Column(String(100), nullable=False) 
    data_criacao = Column(TIMESTAMP, server_default=func.current_timestamp())