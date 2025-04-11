from sqlalchemy.orm import Session
from models.usuario import Usuario
from passlib.hash import bcrypt

class UsuarioDAO:
    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def create(db: Session, email: str, senha: str):
        senha_hash = bcrypt.hash(senha)
        novo_usuario = Usuario(email=email, senha_hash=senha_hash, tipo="aluno")
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
