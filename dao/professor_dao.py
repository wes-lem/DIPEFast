from sqlalchemy.orm import Session
from models.professor import Professor
from models.usuario import Usuario
from passlib.hash import bcrypt

class ProfessorDAO:
    @staticmethod
    def create(db: Session, usuario_id: int, nome: str, campus_id: int, especialidade: str = None, imagem: str = None):
        """Cria um novo professor"""
        professor = Professor(
            id=usuario_id,
            nome=nome,
            campus_id=campus_id,
            especialidade=especialidade,
            imagem=imagem
        )
        db.add(professor)
        db.commit()
        db.refresh(professor)
        return professor

    @staticmethod
    def create_with_usuario(db: Session, email: str, senha: str, nome: str, campus_id: int, especialidade: str = None, imagem: str = None):
        """Cria um novo professor com usuário"""
        # Verificar se email já existe
        if db.query(Usuario).filter(Usuario.email == email).first():
            return None
        
        # Criar usuário
        senha_hash = bcrypt.hash(senha)
        usuario = Usuario(email=email, senha_hash=senha_hash, tipo='professor')
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        
        # Criar professor
        professor = Professor(
            id=usuario.id,
            nome=nome,
            campus_id=campus_id,
            especialidade=especialidade,
            imagem=imagem
        )
        db.add(professor)
        db.commit()
        db.refresh(professor)
        return professor

    @staticmethod
    def get_by_id(db: Session, professor_id: int):
        """Busca um professor por ID"""
        return db.query(Professor).filter(Professor.id == professor_id).first()

    @staticmethod
    def get_by_usuario_id(db: Session, usuario_id: int):
        """Busca um professor por ID do usuário"""
        return db.query(Professor).filter(Professor.id == usuario_id).first()

    @staticmethod
    def get_all(db: Session):
        """Busca todos os professores"""
        return db.query(Professor).all()

    @staticmethod
    def get_by_campus(db: Session, campus_id: int):
        """Busca professores por campus"""
        return db.query(Professor).filter(Professor.campus_id == campus_id).all()

    @staticmethod
    def update(db: Session, professor_id: int, nome: str = None, especialidade: str = None, imagem: str = None, campus_id: int = None):
        """Atualiza um professor"""
        professor = db.query(Professor).filter(Professor.id == professor_id).first()
        if not professor:
            return None
        
        if nome is not None:
            professor.nome = nome
        if especialidade is not None:
            professor.especialidade = especialidade
        if imagem is not None:
            professor.imagem = imagem
        if campus_id is not None:
            professor.campus_id = campus_id
        
        db.commit()
        db.refresh(professor)
        return professor

    @staticmethod
    def delete(db: Session, professor_id: int):
        """Remove um professor (cascade delete do usuário)"""
        professor = db.query(Professor).filter(Professor.id == professor_id).first()
        if not professor:
            return False
        
        # O cascade delete do relacionamento vai remover o professor
        # e o usuário será removido pelo cascade do relacionamento
        db.delete(professor)
        db.commit()
        return True

    @staticmethod
    def get_with_campus(db: Session, professor_id: int):
        """Busca um professor com dados do campus"""
        return db.query(Professor).join(Professor.campus).filter(Professor.id == professor_id).first()

    @staticmethod
    def get_all_with_campus(db: Session):
        """Busca todos os professores com dados do campus"""
        return db.query(Professor).join(Professor.campus).all()
