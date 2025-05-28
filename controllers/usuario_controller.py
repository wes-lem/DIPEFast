from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from dao.usuario_dao import UsuarioDAO
from dao.database import get_db
from fastapi.templating import Jinja2Templates
from models.aluno import Aluno
from models.usuario import Usuario
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login_page(request: Request):
    erro = request.query_params.get("erro", None)
    return templates.TemplateResponse("aluno/login.html", {"request": request, "erro": erro})

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
            {"request": request, "error": "Email ou senha inválidos"}
        )
    
    # Se o usuário for do tipo "aluno", verificar se está cadastrado em "alunos"
    if usuario.tipo == "aluno":
        aluno = db.query(Aluno).filter(Aluno.idUser == usuario.id).first()
        if not aluno:
            return RedirectResponse(
                url=f"/cadastro/aluno/{usuario.id}", status_code=303
            )
    
    # Criar sessão
    response = RedirectResponse(
        url="/gestor/dashboard" if usuario.tipo == "gestor" else "/perfil",
        status_code=303
    )
    response.set_cookie(
        key="session_user", value=str(usuario.id), httponly=True
    )
    
    return response


@router.post("/sair")
def logout(request: Request, response: Response):
    # Verifica se o cookie está presente antes de remover
    session_user = request.cookies.get("session_user")

    if session_user:
        print(f"🔍 Cookie encontrado antes do logout: {session_user}")
    else:
        print("❌ Nenhum cookie encontrado antes do logout.")
        return RedirectResponse(url="/login", status_code=303)

    # Remove o cookie definindo a expiração para o passado
    response.delete_cookie("session_user", path="/")

    # Verifica se o cookie foi removido imediatamente
    session_user_after = request.cookies.get("session_user")

    if session_user_after:
        print("❌ O cookie ainda está presente após a tentativa de remoção.")
        return RedirectResponse(url="/login", status_code=303)

    print("✅ Cookie 'session_user' removido com sucesso.")

    # Redireciona para a página de login após a remoção do cookie
    return RedirectResponse(url="/login", status_code=303)


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

@router.get("gestor/dashboard")
def dashboard(request: Request, user_id: str = Depends(verificar_sessao)):
    # Se não for verificado o id do usuário, desfaz o login
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        "gestor/dashboard_gestor.html",
        {"request": request, "user_id": user_id}
    )
