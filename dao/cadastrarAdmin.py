from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from models.usuario import Usuario
from database import SessionLocal


# Função para criar um gestor no banco de dados
def cadastrar_gestor(email: str, senha: str, db: Session):
    # Gera o hash da senha usando bcrypt
    senha_hash = bcrypt.hash(senha)

    # Cria o gestor (usuário do tipo 'gestor')
    gestor = Usuario(email=email, senha_hash=senha_hash, tipo="gestor")

    # Adiciona o novo gestor no banco de dados
    db.add(gestor)
    db.commit()
    db.refresh(gestor)

    return gestor


# Função principal para execução
def main():
    # Cria a sessão com o banco de dados
    db = SessionLocal()

    # Dados do gestor que será cadastrado
    email = "cesar@dipe.com"
    senha = "@dipe2025"  # Senha do gestor que será convertida em hash

    # Cadastra o gestor
    gestor_criado = cadastrar_gestor(email, senha, db)

    print(f"Gestor cadastrado: {gestor_criado.id} - {gestor_criado.nome}")

    # Fecha a sessão do banco de dados
    db.close()


# Executa a função principal
if __name__ == "__main__":
    main()
