import os
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from dao.database import get_db
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlalchemy import func
from sqlalchemy.orm import aliased
import shutil

from models.resultado import Resultado
from models.questao import Questao
from models.prova import Prova
from models.aluno import Aluno



UPLOAD_DIR = Path("templates/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/provas/cadastrar")
def cadastro_prova_page(request: Request):
    return templates.TemplateResponse("cadastro_prova.html", {"request": request})

async def salvar_imagem(imagem: UploadFile, nome_arquivo: str):
    caminho_arquivo = UPLOAD_DIR / nome_arquivo
    with caminho_arquivo.open("wb") as buffer:
        buffer.write(await imagem.read())
    return f"/static/uploads/{nome_arquivo}"

@router.post("/provas/cadastrar")
async def cadastrar_prova(
    request: Request,
    materia: str = Form(...),
    db: Session = Depends(get_db),
    enunciados: list[str] = Form(...),
    imagens: list[UploadFile] = File(None),
    alternativas_A: list[str] = Form(...),
    alternativas_B: list[str] = Form(...),
    alternativas_C: list[str] = Form(...),
    alternativas_D: list[str] = Form(...),
    alternativas_E: list[str] = Form(...),
    corretas_1: str = Form(...),
    corretas_2: str = Form(...),
    corretas_3: str = Form(...),
    corretas_4: str = Form(...),
    corretas_5: str = Form(...),
    corretas_6: str = Form(...),
    corretas_7: str = Form(...),
    corretas_8: str = Form(...),
    corretas_9: str = Form(...),
    corretas_10: str = Form(...),
    corretas_11: str = Form(...),
    corretas_12: str = Form(...),
    corretas_13: str = Form(...),
    corretas_14: str = Form(...),
    corretas_15: str = Form(...),
):
    """
    Rota para cadastrar uma prova e suas 15 questões.
    """
    
    form_data = await request.form()
    print("📌 Dados do formulário recebidos:", dict(form_data))

    # Criar a prova
    nova_prova = Prova(materia=materia)
    db.add(nova_prova)
    db.commit()
    db.refresh(nova_prova)

    corretas = [
        corretas_1, corretas_2, corretas_3, corretas_4, corretas_5,
        corretas_6, corretas_7, corretas_8, corretas_9, corretas_10,
        corretas_11, corretas_12, corretas_13, corretas_14, corretas_15
    ]

    # Armazenar os dados das imagens antes de gravar no banco
    imagens_salvas = []

    for i in range(15):
        image_path = None

        if imagens and imagens[i] and imagens[i].filename:
            filename = f"questao_{nova_prova.id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagens[i].filename).suffix}"
            file_location = UPLOAD_DIR / filename

            conteudo = await imagens[i].read()  # 🟡 Lê o conteúdo da imagem só uma vez
            imagens_salvas.append((conteudo, file_location))

            image_path = f"static/uploads/{filename}"


        nova_questao = Questao(
            prova_id=nova_prova.id,
            enunciado=enunciados[i],
            imagem=image_path,
            opcao_a=alternativas_A[i],
            opcao_b=alternativas_B[i],
            opcao_c=alternativas_C[i],
            opcao_d=alternativas_D[i],
            opcao_e=alternativas_E[i],
            resposta_correta=corretas[i]
        )
        db.add(nova_questao)

    db.commit()  
    
    for conteudo, file_path in imagens_salvas:
        with open(file_path, "wb") as buffer:
            buffer.write(conteudo)


    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/alunos")
def listar_alunos(
    request: Request,
    db: Session = Depends(get_db),
    curso: Optional[str] = Query(None),
    ano: Optional[str] = Query(None),
    situacao: Optional[str] = Query(None),
):
    # Criando alias para as provas
    portugues = aliased(Prova)
    matematica = aliased(Prova)
    ciencias = aliased(Prova)

    # Query principal para buscar alunos
    query = db.query(
        Aluno,
        func.coalesce(
            db.query(Resultado.acertos)
            .join(portugues, Resultado.prova_id == portugues.id)
            .filter(portugues.materia == "Português", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_portugues"),
        func.coalesce(
            db.query(Resultado.acertos)
            .join(matematica, Resultado.prova_id == matematica.id)
            .filter(matematica.materia == "Matemática", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_matematica"),
        func.coalesce(
            db.query(Resultado.acertos)
            .join(ciencias, Resultado.prova_id == ciencias.id)
            .filter(ciencias.materia == "Ciências", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_ciencias"),
    ).select_from(Aluno)

    # Aplicando os filtros se existirem
    if curso:
        query = query.filter(Aluno.curso == curso)
    if ano:
        query = query.filter(Aluno.ano == ano)
    if situacao:
        query = query.filter(Aluno.situacao == situacao)

    alunos = query.all()

    return templates.TemplateResponse(
        "gestor_alunos.html",
        {
            "request": request,
            "alunos": alunos
        },
    )

@router.get("/alunos/cadastrar")
def cadastro_prova_page(request: Request):
    return templates.TemplateResponse("gestor_cadastro.html", {"request": request})

# Uploads de imagens
@router.post("/alunos/upload/{aluno_id}")
def upload_imagem(aluno_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return {"error": "Aluno não encontrado"}

    # Salvar a imagem
    filename = f"aluno_{aluno_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Atualizar o caminho da imagem no banco
    aluno.imagem = f"static/uploads/{filename}"
    db.commit()

    return {"message": "Imagem enviada com sucesso!", "path": aluno.imagem}