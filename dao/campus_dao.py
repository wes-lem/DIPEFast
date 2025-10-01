from sqlalchemy.orm import Session
from models.campus import Campus

class CampusDAO:
    @staticmethod
    def create(db: Session, nome: str, endereco: str = None):
        """Cria um novo campus"""
        campus = Campus(nome=nome, endereco=endereco)
        db.add(campus)
        db.commit()
        db.refresh(campus)
        return campus

    @staticmethod
    def get_by_id(db: Session, campus_id: int):
        """Busca um campus por ID"""
        return db.query(Campus).filter(Campus.id == campus_id).first()

    @staticmethod
    def get_all(db: Session):
        """Busca todos os campus ativos"""
        return db.query(Campus).filter(Campus.ativo == True).all()

    @staticmethod
    def get_all_including_inactive(db: Session):
        """Busca todos os campus (incluindo inativos)"""
        return db.query(Campus).all()

    @staticmethod
    def update(db: Session, campus_id: int, nome: str = None, endereco: str = None, ativo: bool = None):
        """Atualiza um campus"""
        campus = db.query(Campus).filter(Campus.id == campus_id).first()
        if not campus:
            return None
        
        if nome is not None:
            campus.nome = nome
        if endereco is not None:
            campus.endereco = endereco
        if ativo is not None:
            campus.ativo = ativo
        
        db.commit()
        db.refresh(campus)
        return campus

    @staticmethod
    def delete(db: Session, campus_id: int):
        """Desativa um campus (soft delete)"""
        campus = db.query(Campus).filter(Campus.id == campus_id).first()
        if not campus:
            return False
        
        campus.ativo = False
        db.commit()
        return True

    @staticmethod
    def hard_delete(db: Session, campus_id: int):
        """Remove permanentemente um campus"""
        campus = db.query(Campus).filter(Campus.id == campus_id).first()
        if not campus:
            return False
        
        db.delete(campus)
        db.commit()
        return True
