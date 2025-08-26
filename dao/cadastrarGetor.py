import bcrypt
from dao.database import sessionlocal
from models.usuario import Usuario
from models.gestor import Gestor
from sqlalchemy.exc import IntegrityError

def criar_gestor(email, senha, nome, imagem=None):
    # Criar sessão
    db = sessionlocal()
    try:
        # Gerar hash da senha com bcrypt
        senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Criar usuário base
        usuario = Usuario(
            email=email,
            senha_hash=senha_hash,
            tipo="Gestor"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)  # Pega o ID gerado

        # Criar registro na tabela gestores
        gestor = Gestor(
            id=usuario.id,
            nome=nome,
            imagem=imagem
        )
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
    # Exemplo de uso
    criar_gestor(
        email="gestor@dipe.com",
        senha="@dipe2025",
        nome="Gestor"
    )
