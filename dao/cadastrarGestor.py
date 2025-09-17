import bcrypt
from sqlalchemy.orm import Session
import models
from .database import SessionLocal
from models import Usuario, Gestor

def criar_gestor_padrao():
    db: Session = SessionLocal()
    try:
        email_gestor_padrao = "gestor@dipe.com"
        
        usuario_existente = db.query(Usuario).filter(Usuario.email == email_gestor_padrao).first()
        
        if not usuario_existente:
            print("Criando gestor padrão...")
            
            senha_padrao_texto = "@dipe2025"
            nome_padrao = "Gestor"
            
            senha_hash = bcrypt.hashpw(senha_padrao_texto.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            novo_usuario = Usuario(email=email_gestor_padrao, senha_hash=senha_hash, tipo="gestor")
            db.add(novo_usuario)
            
            novo_gestor = Gestor(nome=nome_padrao, usuario=novo_usuario)
            db.add(novo_gestor)
            
            db.commit()
            print("✅ Gestor padrão criado com sucesso!")
        else:
            print("ℹ️ Gestor padrão já existe. Nenhuma ação necessária.")

    finally:
        db.close()