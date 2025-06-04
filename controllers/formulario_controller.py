from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import List, Optional

# Importações dos seus DAOs e Models
from dao.database import get_db
from dao.formulario_dao import FormularioDAO
from dao.pergunta_formulario_dao import PerguntaFormularioDAO # Adicionado: DAO de Perguntas
from dao.resposta_formulario_dao import RespostaFormularioDAO
from dao.notificacao_dao import NotificacaoDAO

from models.aluno import Aluno
from models.usuario import Usuario
from models.formulario import Formulario
from models.pergunta_formulario import PerguntaFormulario
from models.notificacao import Notificacao

from controllers.usuario_controller import verificar_sessao
from controllers.gestor_controller import verificar_gestor_sessao 

from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/gestor/formularios", response_class=HTMLResponse)
async def listar_formularios_gestor(request: Request, db: Session = Depends(get_db)):
    """Lista todos os formulários cadastrados para o gestor."""
    formularios = FormularioDAO.get_all(db)
    formularios_info = []
    for form in formularios:
        total_respondedores = RespostaFormularioDAO.get_total_respondedores_by_formulario(db, form.id)
        formularios_info.append({
            "id": form.id,
            "titulo": form.titulo,
            "descricao": form.descricao,
            "data_criacao": form.data_criacao,
            "total_respondedores": total_respondedores
        })
    
    return templates.TemplateResponse(
        "gestor/listar_formularios.html",
        {"request": request, "formularios": formularios_info}
    )

@router.get("/gestor/formularios/cadastrar")
def cadastrar_formulario_page(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Página para o gestor cadastrar um novo formulário."""
    return templates.TemplateResponse(
        "gestor/cadastrar_formulario.html",
        {"request": request}
    )

@router.post("/gestor/formularios/cadastrar")
async def cadastrar_formulario(
    request: Request,
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    perguntas_json: str = Form(...),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cria um novo formulário com suas perguntas e notifica os alunos."""
    try:
        perguntas_data = json.loads(perguntas_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato JSON inválido para perguntas.")

    novo_formulario = FormularioDAO.create_formulario(
        db=db,
        titulo=titulo,
        descricao=descricao
    )

    # Adicionar perguntas
    for i, p_data in enumerate(perguntas_data):
        PerguntaFormularioDAO.create_pergunta(
            db=db,
            formulario_id=novo_formulario.id,
            tipo_pergunta=p_data["tipo"],
            enunciado=p_data["enunciado"],
            opcoes=json.dumps(p_data.get("opcoes")) if p_data.get("opcoes") else None 
            #
        )
        
    alunos = db.query(Aluno).all()
    for aluno in alunos:
        NotificacaoDAO.criar_notificacao_para_novo_formulario(
            db=db,
            aluno_id=aluno.idAluno,
            formulario_id=novo_formulario.id,
            titulo_formulario=titulo
        )

    return RedirectResponse(url="/gestor/formularios", status_code=303)

@router.get("/gestor/formularios/{formulario_id}/respostas")
def ver_alunos_que_responderam(
    request: Request,
    formulario_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista os alunos que responderam a um formulário específico."""
    formulario = FormularioDAO.get_by_id(db, formulario_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")
    
    alunos_respondedores = RespostaFormularioDAO.get_alunos_who_responded_formulario(db, formulario_id)
    
    return templates.TemplateResponse(
        "gestor/alunos_respondedores.html",
        {"request": request, "formulario": formulario, "alunos": alunos_respondedores}
    )

@router.get("/gestor/formularios/{formulario_id}/respostas/{aluno_id}")
def ver_resposta_detalhada_aluno(
    request: Request,
    formulario_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Exibe as respostas detalhadas de um aluno para um formulário específico."""
    formulario = FormularioDAO.get_by_id(db, formulario_id)
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    
    if not formulario or not aluno:
        raise HTTPException(status_code=404, detail="Formulário ou Aluno não encontrado.")

    respostas_com_perguntas = RespostaFormularioDAO.get_respostas_by_aluno_and_formulario(db, aluno_id, formulario_id)
    
    respostas_formatadas = []
    for resposta_item in respostas_com_perguntas:
        resposta_obj = resposta_item[0]
        enunciado = resposta_item[1]
        tipo_pergunta = resposta_item[2]
        opcoes_json = resposta_item[3]

        resposta_dada = resposta_obj.resposta_texto
        if tipo_pergunta == 'multipla_escolha' and resposta_obj.resposta_opcoes:
            try:
                resposta_dada = json.loads(resposta_obj.resposta_opcoes)
            except json.JSONDecodeError:
                resposta_dada = resposta_obj.resposta_opcoes
        elif tipo_pergunta in ['selecao_unica', 'sim_nao'] and resposta_obj.resposta_texto:
            resposta_dada = resposta_obj.resposta_texto
        
        respostas_formatadas.append({
            "enunciado": enunciado,
            "tipo_pergunta": tipo_pergunta,
            "resposta_dada": resposta_dada,
            "opcoes_pergunta": json.loads(opcoes_json) if opcoes_json else None
        })

    return templates.TemplateResponse(
        "gestor/detalhes_respostas_aluno.html",
        {
            "request": request,
            "formulario": formulario,
            "aluno": aluno,
            "respostas": respostas_formatadas
        }
    )

@router.get("/aluno/formularios")
async def listar_formularios_aluno(
    request: Request, 
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Lista todos os formulários disponíveis para o aluno logado."""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    
    # Verifica formulários não respondidos e cria notificações
    NotificacaoDAO.verificar_formularios_nao_respondidos(db)
    
    formularios = FormularioDAO.get_all(db)
    formularios_com_status = []
    
    for formulario in formularios:
        ja_respondeu = RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, formulario.id)
        formularios_com_status.append({
            "formulario": formulario,
            "ja_respondeu": ja_respondeu
        })
    
    return templates.TemplateResponse(
        "aluno/formularios.html",
        {"request": request, "formularios": formularios_com_status}
    )

@router.get("/aluno/formularios/{formulario_id}")
def responder_formulario_page(
    request: Request,
    formulario_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Página para o aluno responder um formulário específico."""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    formulario = FormularioDAO.get_by_id(db, formulario_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado.")

    # Verificar se já respondeu
    if RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, formulario.id):
        NotificacaoDAO.marcar_notificacao_como_lida(db, aluno.idAluno, link=f"/aluno/formularios/{formulario_id}")
        return templates.TemplateResponse(
            "aluno/formulario_ja_respondido.html",
            {"request": request, "formulario": formulario}
        )

    perguntas = PerguntaFormularioDAO.get_by_formulario(db, formulario_id) 

    return templates.TemplateResponse(
        "aluno/responder_formulario.html",
        {
            "request": request,
            "formulario": formulario,
            "perguntas": perguntas,
            "aluno": aluno
        }
    )

@router.post("/aluno/formularios/{formulario_id}/responder")
async def enviar_respostas(
    request: Request,
    formulario_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Processa as respostas do aluno para um formulário."""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    if RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, formulario_id):
        raise HTTPException(status_code=400, detail="Você já respondeu este formulário.")

    form_data = await request.form()
    perguntas = PerguntaFormularioDAO.get_by_formulario(db, formulario_id)

    for pergunta in perguntas:
        resposta_input = form_data.get(f"pergunta_{pergunta.id}")
        
        if pergunta.tipo_pergunta == 'multipla_escolha':
            respostas_checkbox = form_data.getlist(f"pergunta_{pergunta.id}")
            if respostas_checkbox:
                RespostaFormularioDAO.create_resposta(
                    db=db,
                    aluno_id=aluno.idAluno,
                    formulario_id=formulario_id,
                    pergunta_id=pergunta.id,
                    resposta_opcoes=json.dumps(respostas_checkbox)
                )
            
        elif resposta_input is not None: 
            RespostaFormularioDAO.create_resposta(
                db=db,
                aluno_id=aluno.idAluno,
                formulario_id=formulario_id,
                pergunta_id=pergunta.id,
                resposta_texto=str(resposta_input)
            )

    db.commit() 
    
    NotificacaoDAO.marcar_notificacao_como_lida(db, aluno.idAluno, link=f"/aluno/formularios/{formulario_id}")

    return RedirectResponse(url="/aluno/formularios", status_code=303)

@router.post("/aluno/formularios/{formulario_id}/enviar-respostas")
async def enviar_respostas(
    request: Request,
    formulario_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Processa as respostas enviadas pelo aluno."""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    
    # Verifica se o aluno já respondeu
    if RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, formulario_id):
        return RedirectResponse(url="/aluno/formularios", status_code=303)
    
    # Busca o formulário e suas perguntas
    formulario = FormularioDAO.get_by_id(db, formulario_id)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    
    perguntas = PerguntaFormularioDAO.get_by_formulario(db, formulario_id)
    
    # Processa o formulário
    form_data = await request.form()
    
    try:
        for pergunta in perguntas:
            resposta = form_data.get(f"resposta_{pergunta.id}")
            
            if pergunta.tipo_pergunta == 'multipla_escolha':
                # Para múltipla escolha, o valor vem como lista
                resposta_opcoes = form_data.getlist(f"resposta_{pergunta.id}")
                if resposta_opcoes:
                    RespostaFormularioDAO.create_resposta(
                        db=db,
                        aluno_id=aluno.idAluno,
                        formulario_id=formulario_id,
                        pergunta_id=pergunta.id,
                        resposta_opcoes=json.dumps(resposta_opcoes)
                    )
            else:
                # Para outros tipos, o valor vem como string
                if resposta:
                    RespostaFormularioDAO.create_resposta(
                        db=db,
                        aluno_id=aluno.idAluno,
                        formulario_id=formulario_id,
                        pergunta_id=pergunta.id,
                        resposta_texto=resposta
                    )
        
        # Marca a notificação como lida APÓS salvar todas as respostas
        NotificacaoDAO.marcar_notificacao_como_lida(db, aluno.idAluno, link=f"/aluno/formularios/{formulario_id}")
        
        db.commit()
        return RedirectResponse(url="/aluno/formularios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))