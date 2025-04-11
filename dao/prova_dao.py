from sqlalchemy.orm import Session
from models.prova import Prova

class ProvaDAO:
    @staticmethod
    def get_all(db: Session):
        return db.query(Prova).all()

    @staticmethod
    def get_by_id(db: Session, prova_id: int):
        return db.query(Prova).filter(Prova.id == prova_id).first()

    @staticmethod
    def create(db: Session, nome: str):
        nova_prova = Prova(nome=nome)
        db.add(nova_prova)
        db.commit()
        db.refresh(nova_prova)
        return nova_prova
