from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dao.database import get_db
from fastapi.templating import Jinja2Templates
from models.usuario import Usuario
from models.aluno import Aluno
from dao.aluno_dao import AlunoDAO
from dao.usuario_dao import UsuarioDAO
from datetime import datetime
from models.prova import Prova
from models.resultado import Resultado
from fastapi import File, UploadFile
import os
import shutil

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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

@router.get("/cadastro")
def cadastro_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

# Cadastro de usuário
@router.post("/cadastro")
def cadastro(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):

    usuario_criado = UsuarioDAO.create(db, email, senha)

    # Redireciona para a página de cadastro do aluno com o id do usuário
    return RedirectResponse(url=f"/cadastro/aluno/{usuario_criado.id}", status_code=303)


# Rota para a página de cadastro de aluno, onde o aluno preenche seus dados
@router.get("/cadastro/aluno/{idUser}")
def cadastro_aluno_page(request: Request, idUser: int):
    return templates.TemplateResponse(
        "cadastro_aluno.html", {"request": request, "idUser": idUser}
    )

@router.post("/cadastro/aluno/{idUser}")
def cadastrar_aluno(
    idUser: int,
    nome: str = Form(...),
    ano: int = Form(...),
    curso: str = Form(...),
    idade: int = Form(...),
    municipio: str = Form(...),
    zona: str = Form(...),
    origem_escolar: str = Form(...),
    imagem: UploadFile = File(None),  # Opcional
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == idUser).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Validação básica
    if curso not in ["Redes de Computadores", "Agropecuária"]:
        raise HTTPException(status_code=400, detail="Curso inválido")

    # Salvar imagem (se houver)
    imagem_path = None
    if imagem:
        upload_dir = os.path.join("templates", "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # Cria o caminho absoluto da imagem a ser salva
        imagem_path = os.path.join(upload_dir, f"{idUser}_{imagem.filename}")

        with open(imagem_path, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)

        # Caminho relativo para salvar no banco (para uso em HTML)
        imagem_relativa = imagem_path.replace("templates/", "/")
    else:
        imagem_relativa = None

    # Criação do aluno
    AlunoDAO.create(
        db,
        idUser=idUser,
        nome=nome,
        ano=ano,
        curso=curso,
        idade=idade,
        municipio=municipio,
        zona=zona,
        origem_escolar=origem_escolar,
        imagem=imagem_relativa
    )

    return RedirectResponse(url="/login", status_code=303)

@router.get("/perfil")
def perfil(
    request: Request,
    user_id: str = Depends(verificar_sessao),
    db: Session = Depends(get_db),
):
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # Obtém os dados do aluno
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return {"erro": "Aluno não cadastrado"}

    # Lista fixa de matérias
    materias_fixas = ["Português", "Matemática", "Ciências"]
    materias = []

    for materia in materias_fixas:
        # Busca a prova correspondente no banco
        prova = db.query(Prova).filter(Prova.materia == materia).first()
        
        # A prova está disponível se existir no banco
        prova_disponivel = prova is not None  

        if prova:
            # Obter o resultado da prova do aluno
            resultado = db.query(Resultado).filter(
                Resultado.aluno_id == aluno.idAluno,
                Resultado.prova_id == prova.id
            ).first()
            
            if resultado:
                nota = resultado.acertos
                status = resultado.situacao
            else:
                nota = None
                status = "Não realizada"
            
            url_prova = f"/prova/{prova.id}"
        else:
            nota = None
            status = "Ainda não há provas disponíveis"
            url_prova = "#"

        # Adiciona a matéria na lista com a chave prova_disponivel
        materias.append({
            "nome": materia,
            "nota": nota,
            "status": status,
            "url_prova": url_prova,
            "prova_disponivel": prova_disponivel  # Apenas verifica se a prova existe
        })

    # Retorna as informações para o template
    return templates.TemplateResponse(
        "perfil.html",
        {
            "request": request,
            "id": aluno.idAluno,
            "nome": aluno.nome,
            "imagem": aluno.imagem,
            "idade": aluno.idade,
            "municipio": aluno.municipio,
            "ano": aluno.ano,
            "curso": aluno.curso,
            "materias": materias,
        },
    )
