import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# Configuração do banco de dados MySQL
# Formato: mysql+pymysql://usuario:senha@host:porta/nome_banco
DATABASE_URL="mysql+pymysql://root:@localhost:3306/dipe" 
# Criar engine e sessão
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo Usuario
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)

# Modelo Gestor
class Gestor(Base):
    __tablename__ = "gestores"
    id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    nome = Column(String(100), nullable=False)
    imagem = Column(String(255), nullable=True)

def criar_gestor(email, senha, nome, imagem=None):
    db = SessionLocal()
    try:
        # Gerar hash da senha
        senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Criar usuário
        usuario = Usuario(email=email, senha_hash=senha_hash, tipo="Gestor")
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # Criar gestor
        gestor = Gestor(id=usuario.id, nome=nome, imagem=imagem)
        db.add(gestor)
        db.commit()

        print(f"✅ Gestor '{nome}' criado com sucesso! ID: {usuario.id}")
    except IntegrityError:
        db.rollback()
        print("❌ Erro: já existe um usuário com este email.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar gestor: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # 🔹 Altere os dados abaixo para o gestor que deseja criar
    criar_gestor(
        email="gestor@dipe.com",
        senha="@dipe2025",
        nome="Gestor"
    )
