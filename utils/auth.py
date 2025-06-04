from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from dao.database import get_db
from models.usuario import Usuario
from controllers.usuario_controller import verificar_sessao

def verificar_gestor_sessao(request: Request, db: Session = Depends(get_db)):
    """
    Dependência para verificar se o usuário na sessão é um gestor.
    Redireciona para a página de login se não for.
    """
    session_user_id = verificar_sessao(request)  # Reutiliza a verificação de sessão básica
    usuario = db.query(Usuario).filter(Usuario.id == int(session_user_id)).first()
    if not usuario or usuario.tipo != "gestor":
        raise HTTPException(
            status_code=303,
            detail="Acesso não autorizado para gestores",
            headers={"Location": "/login?erro=Acesso nao autorizado"},
        )
    return usuario.id 