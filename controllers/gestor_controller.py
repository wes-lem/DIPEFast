import os
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from dao.database import get_db
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlalchemy import func, distinct
from sqlalchemy.orm import aliased
import shutil
import json

from models.resultado import Resultado
from models.questao import Questao
from models.prova import Prova
from models.aluno import Aluno



UPLOAD_DIR = Path("templates/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/provas/cadastrar")
def cadastro_prova_page(request: Request, db: Session = Depends(get_db)):
    # Buscar todas as provas cadastradas com suas questões
    provas = db.query(Prova).all()
    provas_info = []
    
    for prova in provas:
        questoes = db.query(Questao).filter(Questao.prova_id == prova.id).all()
        # Normalizar a string da matéria
        materia = prova.materia.strip()
        materia = materia.replace('\u00eas', 'ês')  # Corrigir codificação do 'ês'
        provas_info.append({
            'id': prova.id,
            'materia': materia,
            'data_criacao': prova.data_criacao.strftime('%d/%m/%Y'),
            'questoes': len(questoes)
        })
    
    print("Provas encontradas:", provas_info)  # Debug
    
    return templates.TemplateResponse(
        "gestor/cadastro_prova.html", 
        {
            "request": request,
            "provas_info": provas_info
        }
    )

async def salvar_imagem(imagem: UploadFile, nome_arquivo: str):
    upload_dir = os.path.join("templates", "static", "uploads", "provas")
    os.makedirs(upload_dir, exist_ok=True)
    caminho_arquivo = os.path.join(upload_dir, nome_arquivo)
    with open(caminho_arquivo, "wb") as buffer:
        buffer.write(await imagem.read())
    return f"/static/uploads/provas/{nome_arquivo}"

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
            file_location = os.path.join("templates", "static", "uploads", "provas", filename)

            conteudo = await imagens[i].read()  # 🟡 Lê o conteúdo da imagem só uma vez
            imagens_salvas.append((conteudo, file_location))

            image_path = f"static/uploads/provas/{filename}"


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

    return RedirectResponse(url="/gestor/dashboard", status_code=303)

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
        "gestor/gestor_alunos.html",
        {
            "request": request,
            "alunos": alunos
        },
    )

@router.get("/alunos/cadastrar")
def cadastro_prova_page(request: Request):
    return templates.TemplateResponse("gestor/gestor_cadastro.html", {"request": request})

# Uploads de imagens
@router.post("/alunos/upload/{aluno_id}")
def upload_imagem(aluno_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        return {"error": "Aluno não encontrado"}

    # Salvar a imagem
    filename = f"aluno_{aluno_id}_{file.filename}"
    # Caminho completo para salvar o arquivo
    file_path = os.path.join("templates", "static", "uploads", "alunos", filename)
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Atualizar o caminho da imagem no banco (apenas o path relativo)
    aluno.imagem = f"static/uploads/alunos/{filename}"
    db.commit()

    return {"message": "Imagem enviada com sucesso!", "path": aluno.imagem}

@router.get("/gestor/dashboard", response_class=HTMLResponse)
async def dashboard_gestor(request: Request, db: Session = Depends(get_db)):
    try:
        # Desempenho por disciplina
        desempenho_disciplina = db.query(
            Prova.materia,
            func.avg(Resultado.acertos).label('media_acertos')
        ).join(Resultado).group_by(Prova.materia).all()

        # Distribuição das notas
        distribuicao_notas = db.query(
            func.floor(Resultado.acertos/5)*5,
            func.count(Resultado.id)
        ).group_by(func.floor(Resultado.acertos/5)*5).all()

        # Comparação entre turmas
        comparacao_turmas = db.query(
            Aluno.curso,
            func.avg(Resultado.acertos).label('media_acertos')
        ).join(Resultado).group_by(Aluno.curso).all()

        # Progressão dos alunos
        progressao_alunos = db.query(
            Prova.data_criacao,
            func.avg(Resultado.acertos).label('media_acertos')
        ).join(Resultado).group_by(Prova.data_criacao).order_by(Prova.data_criacao).all()

        # Número de alunos por turma
        alunos_por_turma = db.query(
            Aluno.curso,
            func.count(Aluno.idAluno)
        ).group_by(Aluno.curso).all()

        # Perfil dos alunos por idade
        perfil_idade = db.query(
            Aluno.idade,
            func.count(Aluno.idAluno)
        ).group_by(Aluno.idade).all()

        # Taxa de participação
        total_alunos = db.query(func.count(Aluno.idAluno)).scalar() or 0
        alunos_completos = db.query(func.count(distinct(Resultado.aluno_id))).scalar() or 0

        # Preparar dados para os gráficos
        dados = {
            'desempenho_disciplina': {
                'labels': [d.materia for d in desempenho_disciplina],
                'data': [float(d.media_acertos) if d.media_acertos is not None else 0 for d in desempenho_disciplina]
            },
            'distribuicao_notas': {
                'labels': [f"{n[0]}-{n[0]+4}" for n in distribuicao_notas],
                'data': [n[1] for n in distribuicao_notas]
            },
            'comparacao_turmas': {
                'labels': [t.curso for t in comparacao_turmas],
                'data': [float(t.media_acertos) if t.media_acertos is not None else 0 for t in comparacao_turmas]
            },
            'progressao_alunos': {
                'labels': [str(p.data_criacao) for p in progressao_alunos],
                'data': [float(p.media_acertos) if p.media_acertos is not None else 0 for p in progressao_alunos]
            },
            'alunos_por_turma': {
                'labels': [t[0] for t in alunos_por_turma],
                'data': [t[1] for t in alunos_por_turma]
            },
            'perfil_idade': {
                'labels': [str(i[0]) for i in perfil_idade],
                'data': [i[1] for i in perfil_idade]
            },
            'taxa_participacao': {
                'labels': ['Completaram', 'Não Completaram'],
                'data': [alunos_completos, total_alunos - alunos_completos]
            }
        }

        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {
                "request": request,
                "dados": json.dumps(dados)
            }
        )
    except Exception as e:
        print(f"Erro ao gerar dashboard: {str(e)}")
        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {
                "request": request,
                "dados": json.dumps({
                    'desempenho_disciplina': {'labels': [], 'data': []},
                    'distribuicao_notas': {'labels': [], 'data': []},
                    'comparacao_turmas': {'labels': [], 'data': []},
                    'progressao_alunos': {'labels': [], 'data': []},
                    'alunos_por_turma': {'labels': [], 'data': []},
                    'perfil_idade': {'labels': [], 'data': []},
                    'taxa_participacao': {'labels': ['Completaram', 'Não Completaram'], 'data': [0, 0]}
                })
            }
        )

@router.get("/provas/editar/{prova_id}")
def editar_prova_page(request: Request, prova_id: int, db: Session = Depends(get_db)):
    # Buscar a prova e suas questões
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        return RedirectResponse(url="/provas/cadastrar", status_code=303)
    
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    
    return templates.TemplateResponse(
        "gestor/editar_prova.html",
        {
            "request": request,
            "prova": prova,
            "questoes": questoes
        }
    )

@router.post("/provas/editar/{prova_id}")
async def editar_prova(
    request: Request,
    prova_id: int,
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
    # Atualizar a prova
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        return RedirectResponse(url="/provas/cadastrar", status_code=303)
    
    prova.materia = materia
    db.commit()
    
    # Atualizar as questões
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    corretas = [
        corretas_1, corretas_2, corretas_3, corretas_4, corretas_5,
        corretas_6, corretas_7, corretas_8, corretas_9, corretas_10,
        corretas_11, corretas_12, corretas_13, corretas_14, corretas_15
    ]
    
    for i, questao in enumerate(questoes):
        if i < len(enunciados):
            questao.enunciado = enunciados[i]
            questao.opcao_a = alternativas_A[i]
            questao.opcao_b = alternativas_B[i]
            questao.opcao_c = alternativas_C[i]
            questao.opcao_d = alternativas_D[i]
            questao.opcao_e = alternativas_E[i]
            questao.resposta_correta = corretas[i]
            
            # Atualizar imagem se fornecida
            if imagens and imagens[i] and imagens[i].filename:
                filename = f"questao_{prova_id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagens[i].filename).suffix}"
                file_location = os.path.join("templates", "static", "uploads", "provas", filename)
                
                conteudo = await imagens[i].read()
                with open(file_location, "wb") as buffer:
                    buffer.write(conteudo)
                
                questao.imagem = f"static/uploads/provas/{filename}"
    
    db.commit()
    return RedirectResponse(url="/provas/cadastrar", status_code=303)

@router.post("/provas/excluir/{prova_id}")
def excluir_prova(prova_id: int, db: Session = Depends(get_db)):
    # Buscar a prova
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        return RedirectResponse(url="/provas/cadastrar", status_code=303)
    
    # Excluir as questões
    db.query(Questao).filter(Questao.prova_id == prova_id).delete()
    
    # Excluir a prova
    db.delete(prova)
    db.commit()
    
    return RedirectResponse(url="/provas/cadastrar", status_code=303)