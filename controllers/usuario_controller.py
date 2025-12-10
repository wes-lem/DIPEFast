from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from dao.database import get_db
from models.aluno import Aluno
from models.usuario import Usuario

# Importar a instância templates do app_config
from app_config import templates

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    erro = request.query_params.get("erro", None)
    sucesso = request.query_params.get("sucesso", None)
    return templates.TemplateResponse("aluno/login.html", {"request": request, "erro": erro, "sucesso": sucesso})

@router.get("/index")
def index_page(request: Request):
    return templates.TemplateResponse("gestor/dashboard_gestor.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario or not bcrypt.verify(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            "aluno/login.html",
            {"request": request, "erro": "Email ou senha inválidos"}
        )
    
    # Se o usuário for do tipo "aluno", verificar se está cadastrado em "alunos"
    if usuario.tipo == "aluno":
        aluno = db.query(Aluno).filter(Aluno.idUser == usuario.id).first()
        if not aluno:
            return RedirectResponse(
                url=f"/cadastro/aluno/{usuario.id}", status_code=303
            )
    
    # Definir URL de redirecionamento baseado no tipo de usuário
    if usuario.tipo == "gestor":
        redirect_url = "/gestor/dashboard"
    elif usuario.tipo == "professor":
        redirect_url = "/professor/dashboard"
    else:  # aluno
        redirect_url = "/perfil"
    
    # Criar sessão
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="session_user", value=str(usuario.id), httponly=True
    )
    
    return response


@router.post("/sair")
def logout(request: Request): # Não precisamos injetar Response aqui
    session_user = request.cookies.get("session_user")
    
    if session_user:
        print(f"🔍 Cookie encontrado: {session_user}")
    else:
        print("❌ Nenhum cookie encontrado, redirecionando mesmo assim.")

    # 2. Cria a resposta de redirecionamento
    response = RedirectResponse(url="/login", status_code=303)
    # 3. Deleta o cookie NA RESPOSTA QUE SERÁ RETORNADA
    response.delete_cookie(key="session_user", path="/")
    
    print("✅ Instrução de remoção de cookie adicionada à resposta.")
    return response


#  Solução correta para verificar a sessão
def verificar_sessao(request: Request):
    session_user = request.cookies.get("session_user")
    if not session_user:
        print("❌ Tentativa de acesso sem sessão ativa!")
        # Redireciona para o login com o erro de "Usuário não autenticado"
        raise HTTPException(
            status_code=303,
            detail="Usuário não autenticado",
            headers={"Location": "/login?erro=Usuario nao autenticado"},
        )
    return session_user  # Retorna o ID do usuário para uso na rota
