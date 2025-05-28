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
from sqlalchemy import func, distinct, and_
from sqlalchemy.orm import aliased
import shutil
import json
import random

from models.resultado import Resultado
from models.questao import Questao
from models.prova import Prova
from models.aluno import Aluno
from models.resposta import Resposta



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
        # Criando alias para as provas
        portugues = aliased(Prova)
        matematica = aliased(Prova)
        ciencias = aliased(Prova)

        # Dados para os cards
        total_alunos = db.query(func.count(Aluno.idAluno)).scalar() or 0
        total_provas = db.query(func.count(distinct(Resultado.prova_id))).scalar() or 0
        
        # Calcular média geral
        resultados = db.query(Resultado.acertos).all()
        media_geral = 0
        total_suficiente = 0
        if resultados:
            media_geral = sum(r.acertos for r in resultados) / len(resultados)
            total_suficiente = sum(1 for r in resultados if r.acertos >= 7)
            percentual_suficiente = (total_suficiente / len(resultados)) * 100
        else:
            percentual_suficiente = 0
            
        cards = {
            'total_alunos': total_alunos,
            'total_provas': total_provas,
            'media_geral': f"{media_geral:.1f}",
            'percentual_suficiente': f"{percentual_suficiente:.1f}"
        }

        # Dados para os gráficos com cores personalizadas
        cores = {
            'portugues': 'rgba(255, 99, 132, 0.8)',
            'matematica': 'rgba(54, 162, 235, 0.8)',
            'ciencias': 'rgba(255, 206, 86, 0.8)',
            'urbana': 'rgba(75, 192, 192, 0.8)',
            'rural': 'rgba(153, 102, 255, 0.8)'
        }

        # Distribuição por zona
        zona_distribuicao = {
            'labels': ['Urbana', 'Rural'],
            'data': [
                db.query(Aluno).filter(Aluno.zona == 'urbana').count(),
                db.query(Aluno).filter(Aluno.zona == 'rural').count()
            ],
            'cores': [cores['urbana'], cores['rural']]
        }

        # Distribuição por município
        municipios = db.query(Aluno.municipio, func.count(Aluno.idAluno)).group_by(Aluno.municipio).all()
        cidade_distribuicao = {
            'labels': [m[0] for m in municipios],
            'data': [m[1] for m in municipios]
        }

        # Perfil por idade
        idades = db.query(Aluno.idade, func.count(Aluno.idAluno)).group_by(Aluno.idade).all()
        perfil_idade = {
            'labels': [str(i[0]) for i in idades],
            'data': [i[1] for i in idades]
        }

        # Desempenho por disciplina
        desempenho_disciplina = {
            'labels': ['Português', 'Matemática', 'Ciências'],
            'data': [
                float(db.query(func.avg(Resultado.acertos)).filter(Resultado.prova_id == portugues.id).scalar() or 0),
                float(db.query(func.avg(Resultado.acertos)).filter(Resultado.prova_id == matematica.id).scalar() or 0),
                float(db.query(func.avg(Resultado.acertos)).filter(Resultado.prova_id == ciencias.id).scalar() or 0)
            ]
        }

        # Distribuição das notas
        distribuicao_notas = {
            'labels': ['Insuficiente', 'Regular', 'Suficiente'],
            'data': [
                db.query(func.count(Resultado.id)).filter(Resultado.acertos <= 5).scalar() or 0,
                db.query(func.count(Resultado.id)).filter(and_(Resultado.acertos > 5, Resultado.acertos <= 10)).scalar() or 0,
                db.query(func.count(Resultado.id)).filter(Resultado.acertos > 10).scalar() or 0
            ]
        }

        # Progressão dos Alunos (exemplo: média geral por ano)
        anos = db.query(Aluno.ano).distinct().order_by(Aluno.ano).all()
        anos_labels = [str(a[0]) for a in anos]
        progressao_alunos_data = []
        for ano in anos_labels:
            alunos_ano = db.query(Aluno.idAluno).filter(Aluno.ano == int(ano)).all()
            if alunos_ano:
                ids = [a[0] for a in alunos_ano]
                resultados_ano = db.query(Resultado.acertos).filter(Resultado.aluno_id.in_(ids)).all()
                if resultados_ano:
                    media_ano = sum(r.acertos for r in resultados_ano) / len(resultados_ano)
                else:
                    media_ano = 0
            else:
                media_ano = 0
            progressao_alunos_data.append(round(media_ano, 2))
        progressao_alunos = {
            'labels': anos_labels,
            'data': progressao_alunos_data
        }

        # Comparação entre Turmas (exemplo: média geral por curso)
        cursos = db.query(Aluno.curso).distinct().all()
        cursos_labels = [c[0] for c in cursos]
        comparacao_turmas_data = []
        for curso in cursos_labels:
            alunos_curso = db.query(Aluno.idAluno).filter(Aluno.curso == curso).all()
            if alunos_curso:
                ids = [a[0] for a in alunos_curso]
                resultados_curso = db.query(Resultado.acertos).filter(Resultado.aluno_id.in_(ids)).all()
                if resultados_curso:
                    media_curso = sum(r.acertos for r in resultados_curso) / len(resultados_curso)
                else:
                    media_curso = 0
            else:
                media_curso = 0
            comparacao_turmas_data.append(round(media_curso, 2))
        comparacao_turmas = {
            'labels': cursos_labels,
            'data': comparacao_turmas_data
        }

        # Número de Alunos por Turma
        alunos_por_turma_data = []
        for curso in cursos_labels:
            count = db.query(Aluno).filter(Aluno.curso == curso).count()
            alunos_por_turma_data.append(count)
        alunos_por_turma = {
            'labels': cursos_labels,
            'data': alunos_por_turma_data
        }

        # Taxa de Participação (exemplo: alunos que fizeram pelo menos uma prova)
        total_alunos = db.query(func.count(Aluno.idAluno)).scalar() or 0
        alunos_com_resultado = db.query(Resultado.aluno_id).distinct().count()
        taxa_participacao = {
            'labels': ['Participaram', 'Não participaram'],
            'data': [alunos_com_resultado, max(0, total_alunos - alunos_com_resultado)]
        }

        # Top 10 Alunos (maior média)
        alunos = db.query(Aluno).all()
        top_alunos_lista = []
        for aluno in alunos:
            resultados = db.query(Resultado).filter(Resultado.aluno_id == aluno.idAluno).all()
            notas = [r.acertos for r in resultados]
            media = sum(notas) / len(notas) if notas else 0
            top_alunos_lista.append({
                'nome': aluno.nome,
                'turma': aluno.curso,
                'nota_portugues': next((r.acertos for r in resultados if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Português').first()), 0),
                'nota_matematica': next((r.acertos for r in resultados if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Matemática').first()), 0),
                'nota_ciencias': next((r.acertos for r in resultados if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Ciências').first()), 0),
                'media': round(media, 2),
                'foto': aluno.imagem or '/static/img/user.png'
            })
        top_alunos = sorted(top_alunos_lista, key=lambda x: x['media'], reverse=True)[:10]

        dados = {
            'cards': cards,
            'zona_distribuicao': zona_distribuicao,
            'cidade_distribuicao': cidade_distribuicao,
            'perfil_idade': perfil_idade,
            'desempenho_disciplina': desempenho_disciplina,
            'distribuicao_notas': distribuicao_notas,
            'progressao_alunos': progressao_alunos,
            'comparacao_turmas': comparacao_turmas,
            'alunos_por_turma': alunos_por_turma,
            'taxa_participacao': taxa_participacao,
            'top_alunos': top_alunos
        }

        print("Dados sendo enviados para o template:", dados)  # Log para debug

        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {
                "request": request,
                "dados": dados
            }
        )
    except SQLAlchemyError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {"request": request, "erro": "Erro ao carregar os dados"},
            status_code=500
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
    
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()

    # Deletar respostas das questões
    for questao in questoes:
        db.query(Resposta).filter(Resposta.questao_id == questao.id).delete()

    # Deletar as questões
    db.query(Questao).filter(Questao.prova_id == prova_id).delete()

    # Deletar os resultados associados à prova
    db.query(Resultado).filter(Resultado.prova_id == prova_id).delete()

    # Agora sim, deletar a prova
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    db.delete(prova)
    db.commit()
        
    return RedirectResponse(url="/provas/cadastrar", status_code=303)

@router.get("/alunos/{aluno_id}")
def detalhes_aluno(
    request: Request,
    aluno_id: int,
    db: Session = Depends(get_db)
):
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # Buscar notas das provas
    portugues = aliased(Prova)
    matematica = aliased(Prova)
    ciencias = aliased(Prova)

    nota_portugues = db.query(Resultado.acertos).join(portugues, Resultado.prova_id == portugues.id)\
        .filter(portugues.materia == "Português", Resultado.aluno_id == aluno_id).scalar()
    nota_matematica = db.query(Resultado.acertos).join(matematica, Resultado.prova_id == matematica.id)\
        .filter(matematica.materia == "Matemática", Resultado.aluno_id == aluno_id).scalar()
    nota_ciencias = db.query(Resultado.acertos).join(ciencias, Resultado.prova_id == ciencias.id)\
        .filter(ciencias.materia == "Ciências", Resultado.aluno_id == aluno_id).scalar()

    return templates.TemplateResponse(
        "gestor/detalhes_aluno.html",
        {
            "request": request,
            "aluno": aluno,
            "nota_portugues": nota_portugues,
            "nota_matematica": nota_matematica,
            "nota_ciencias": nota_ciencias
        }
    )

@router.post("/gestor/alunos/{aluno_id}/editar")
async def editar_aluno(
    request: Request,
    aluno_id: int,
    nome: str = Form(...),
    idade: int = Form(...),
    municipio: str = Form(...),
    zona: str = Form(...),
    origem_escolar: str = Form(...),
    curso: str = Form(...),
    ano: int = Form(...),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        return RedirectResponse(url="/alunos", status_code=303)
    
    # Atualizar dados básicos
    aluno.nome = nome
    aluno.idade = idade
    aluno.municipio = municipio
    aluno.zona = zona
    aluno.origem_escolar = origem_escolar
    aluno.curso = curso
    aluno.ano = ano
    
    # Atualizar foto se fornecida
    if foto and foto.filename:
        # Deletar foto antiga se existir
        if aluno.imagem and os.path.exists(os.path.join("templates", aluno.imagem)):
            os.remove(os.path.join("templates", aluno.imagem))
        
        # Salvar nova foto
        filename = f"aluno_{aluno.idAluno}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(foto.filename).suffix}"
        file_location = os.path.join("templates", "static", "uploads", "alunos", filename)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        
        conteudo = await foto.read()
        with open(file_location, "wb") as buffer:
            buffer.write(conteudo)
        
        aluno.imagem = f"static/uploads/alunos/{filename}"
    
    db.commit()
    return RedirectResponse(url=f"/alunos/{aluno_id}", status_code=303)