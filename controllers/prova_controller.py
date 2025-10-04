from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from dao.database import get_db
from models.prova import Prova
from models.questao import Questao
from models.resultado import Resultado
from models.resposta import Resposta
from models.aluno import Aluno
from dao.resposta_dao import RespostaDAO
from dao.questao_dao import QuestaoDAO
from dao.resultados_dao import ResultadoDAO
from controllers.usuario_controller import verificar_sessao

# Importar a instância templates do app_config
from app_config import templates

router = APIRouter()

# def verificar_sessao(request: Request):
#     session_user = request.cookies.get("session_user")
#     if not session_user:
#         raise HTTPException(status_code=303, detail="Usuário não autenticado", headers={"Location": "/login"})
#     return session_user

# Listar provas disponíveis para o aluno
@router.get("/provas")
def listar_provas(request: Request, user_id: int = Depends(verificar_sessao), db: Session = Depends(get_db)):
    # Busca a primeira prova cadastrada
    primeira_prova = db.query(Prova).order_by(Prova.id).first()
    
    if not primeira_prova:
        return RedirectResponse(url="/perfil", status_code=303)
    
    # Redireciona para a rota de resultado detalhado da primeira prova
    return RedirectResponse(
        url=f"/prova/{primeira_prova.id}/resultado-detalhado",
        status_code=303
    )

# Página para o aluno responder a prova
@router.get("/prova/{prova_id}")
def responder_prova(request: Request, prova_id: int, db: Session = Depends(get_db)):
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")

    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    if not questoes:
        raise HTTPException(status_code=404, detail="Questões não encontradas")

    return templates.TemplateResponse(
        "aluno/responder_prova.html",
        {
            "request": request,
            "prova": prova,
            "questoes": questoes
        }
    )

@router.post("/prova/{prova_id}/responder")
async def enviar_respostas(
    prova_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(verificar_sessao),
):
    # Verifica se o aluno existe
    aluno = db.query(Aluno).filter_by(idUser=user_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Verifica se o aluno já respondeu essa prova
    resultado_existente = ResultadoDAO.buscar_por_aluno_e_prova(db, aluno_id=aluno.idAluno, prova_id=prova_id)
    if resultado_existente:
        return RedirectResponse(url="/perfil?erro=Ja_respondida", status_code=303)

    form_data = await request.form()
    respostas = {
        int(key.split("_")[1]): value
        for key, value in form_data.items()
        if key.startswith("resposta_")
    }

    acertos = 0

    for questao_id, resposta_aluno in respostas.items():
        questao = db.query(Questao).filter_by(id=questao_id).first()
        if not questao:
            continue

        # Salva a resposta do aluno
        RespostaDAO.create(
            db,
            aluno_id=aluno.idAluno,
            questao_id=questao_id,
            resposta=resposta_aluno.strip().lower()
        )

        if resposta_aluno.strip().lower() == questao.resposta_correta.strip().lower():
            acertos += 1

    # Determina situação
    if acertos <= 5:
        situacao = "Insuficiente"
    elif acertos <= 10:
        situacao = "Regular"
    else:
        situacao = "Suficiente"

    # Salva o resultado
    ResultadoDAO.criar_resultado(
        db=db,
        aluno_id=aluno.idAluno,
        prova_id=prova_id,
        acertos=acertos,
        situacao=situacao
    )

    return RedirectResponse(url="/perfil", status_code=303)

# Listar questões de uma prova
@router.get("/provas/{prova_id}/questoes")
def listar_questoes(request: Request, prova_id: int, db: Session = Depends(get_db)):
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    return templates.TemplateResponse("listar_questoes.html", {"request": request, "questoes": questoes})

# Adicionar questão a uma prova
@router.post("/provas/{prova_id}/questoes")
def adicionar_questao(
    prova_id: int,
    enunciado: str = Form(...),
    alternativa_a: str = Form(...),
    alternativa_b: str = Form(...),
    alternativa_c: str = Form(...),
    alternativa_d: str = Form(...),
    alternativa_e: str = Form(...),
    resposta_correta: str = Form(...),
    db: Session = Depends(get_db),
):
    QuestaoDAO.create(
        db, prova_id, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, resposta_correta
    )
    return RedirectResponse(url=f"/provas/{prova_id}/questoes", status_code=303)

# Nova rota para exibir o resultado detalhado da prova
@router.get("/prova/{prova_id}/resultado-detalhado", response_class=HTMLResponse)
def resultado_detalhado_prova(
    request: Request,
    prova_id: int,
    user_id: int = Depends(verificar_sessao),
    db: Session = Depends(get_db)
):
    # Verifica se o aluno existe
    aluno = db.query(Aluno).filter_by(idUser=user_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Busca a prova
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")

    # Busca as questões da prova
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    if not questoes:
        raise HTTPException(status_code=404, detail="Questões não encontradas")
        
    # Busca as respostas do aluno para esta prova
    respostas_aluno = db.query(Resposta).filter(
        Resposta.aluno_id == aluno.idAluno,
        Resposta.questao_id.in_([q.id for q in questoes])
    ).all()
    
    # Cria um dicionário de respostas do aluno para fácil acesso
    respostas_dict = {resposta.questao_id: resposta.resposta for resposta in respostas_aluno}

    # Buscar resultados do aluno nas matérias fixas
    materias_fixas = ["Português", "Matemática", "Ciências"]
    resumos_materias = []

    for materia_nome in materias_fixas:
        prova_materia = db.query(Prova).filter(Prova.materia == materia_nome).first()
        prova_disponivel = prova_materia is not None
        nota = None
        status = "Ainda não há provas disponíveis"
        url_prova = "#"

        if prova_materia:
            resultado_materia = db.query(Resultado).filter(
                Resultado.aluno_id == aluno.idAluno,
                Resultado.prova_id == prova_materia.id
            ).first()
            
            if resultado_materia:
                nota = float(resultado_materia.acertos)
                status = resultado_materia.situacao
                # Se a prova foi realizada, o link leva para o resultado detalhado
                url_prova = f"/prova/{prova_materia.id}/resultado-detalhado"
            else:
                # Se a prova está disponível mas não realizada, o link leva para a prova
                url_prova = f"/prova/{prova_materia.id}"

        resumos_materias.append({
            "nome": materia_nome,
            "nota": nota,
            "status": status,
            "url_prova": url_prova,
            "prova_disponivel": prova_disponivel
        })

    return templates.TemplateResponse(
        "aluno/resultado_detalhado_prova.html",
        {
            "request": request,
            "prova": prova,
            "questoes": questoes,
            "respostas": respostas_dict,
            "resumos_materias": resumos_materias, # Passa os resumos das matérias para o template
            "aluno_id": aluno.idAluno # Passa o aluno_id para o link do dashboard
        }
    )

# Ver resultado das provas de um aluno
@router.get("/perfil/{aluno_id}/resultado")
def resultado_provas(request: Request, aluno_id: int, db: Session = Depends(get_db)):
    respostas = db.query(Resposta).filter(Resposta.aluno_id == aluno_id).all()
    
    pontuacao = {"Português": 0, "Matemática": 0, "Ciências": 0}
    total_questoes = {"Português": 0, "Matemática": 0, "Ciências": 0}

    for resposta in respostas:
        questao = db.query(Questao).filter(Questao.id == resposta.questao_id).first()
        if questao:
            total_questoes[questao.materia] += 1
            if resposta.resposta == questao.resposta_correta:
                pontuacao[questao.materia] += 1

    situacoes = {}
    for materia, acertos in pontuacao.items():
        if acertos <= 5:
            situacoes[materia] = "Insuficiente"
        elif acertos <= 10:
            situacoes[materia] = "Regular"
        else:
            situacoes[materia] = "Suficiente"

    return templates.TemplateResponse(
        "aluno/resultado.html", {"request": request, "pontuacao": pontuacao, "situacoes": situacoes}
    )

# Rota para redirecionar para o resultado detalhado da primeira prova
@router.get("/prova/1/resultado-detalhado")
def primeira_prova_resultado(
    request: Request,
    user_id: int = Depends(verificar_sessao),
    db: Session = Depends(get_db)
):
    # Busca a primeira prova cadastrada
    primeira_prova = db.query(Prova).order_by(Prova.id).first()
    
    if not primeira_prova:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma prova cadastrada no sistema"
        )
    
    # Redireciona para a rota de resultado detalhado da primeira prova
    return RedirectResponse(
        url=f"/prova/{primeira_prova.id}/resultado-detalhado",
        status_code=303
    )
