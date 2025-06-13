import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from dao.database import get_db
from dao.aluno_dao import AlunoDAO
from dao.usuario_dao import UsuarioDAO
from models.aluno import Aluno
from models.usuario import Usuario
from models.prova import Prova
from models.resultado import Resultado
from models.resposta import Resposta

from controllers.usuario_controller import verificar_sessao

from services.graficos_service import AnalyticsService
from dao.notificacao_dao import NotificacaoDAO
from dao.formulario_dao import FormularioDAO
from dao.resposta_formulario_dao import RespostaFormularioDAO

# Importar a instância templates do app_config
from app_config import templates

UPLOAD_DIR = Path("templates/static/uploads") # Pode ser definido globalmente se usado em outros controllers/DAOs
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # Garante que o diretório existe

router = APIRouter()

@router.get("/cadastro")
def cadastro_page(request: Request):
    return templates.TemplateResponse("aluno/cadastro.html", {"request": request})

@router.post("/cadastro")
def cadastro(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Processa o cadastro de um novo usuário.
    Verifica se o e-mail já existe antes de criar.
    """
    # Verificar se o e-mail já está em uso
    usuario_existente = UsuarioDAO.get_by_email(db, email)
    if usuario_existente:
        # Se o e-mail já existe, retorna para a página de cadastro com uma mensagem de erro
        return templates.TemplateResponse(
            "aluno/cadastro.html",
            {"request": request, "erro": "E-mail já cadastrado. Por favor, use outro e-mail."}
        )

    # Se o e-mail não existe, procede com a criação do usuário
    try:
        usuario_criado = UsuarioDAO.create(db, email, senha)
    except Exception as e:
        # Captura qualquer outro erro que possa ocorrer durante a criação
        print(f"Erro ao criar usuário: {e}")
        return templates.TemplateResponse(
            "aluno/cadastro.html",
            {"request": request, "erro": "Ocorreu um erro ao tentar cadastrar. Tente novamente mais tarde."}
        )

    # Redireciona para a página de cadastro do aluno com o id do usuário recém-criado
    return RedirectResponse(url=f"/cadastro/aluno/{usuario_criado.id}", status_code=303)

# --- Rota /cadastro/aluno/{idUser} (mantida como está, pois o AlunoDAO já lida com a criação) ---
@router.get("/cadastro/aluno/{idUser}")
def cadastro_aluno_page(request: Request, idUser: int):
    return templates.TemplateResponse(
        "aluno/cadastro_aluno.html", {"request": request, "idUser": idUser}
    )

@router.post("/cadastro/aluno/{idUser}")
async def cadastrar_aluno(
    idUser: int,
    nome: str = Form(...),
    ano: int = Form(...),
    curso: str = Form(...),
    idade: int = Form(...),
    municipio: str = Form(...),
    zona: str = Form(...),
    origem_escolar: str = Form(...),
    escola: Optional[str] = Form(None),
    forma_ingresso: Optional[str] = Form(None),
    acesso_internet: Optional[str] = Form(None),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == idUser).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if curso not in ["Redes de Computadores", "Agropecuária", "Partiu IF"]:
        raise HTTPException(status_code=400, detail="Curso inválido")

    imagem_relativa = None
    if imagem and imagem.filename:
        upload_dir_aluno = os.path.join(UPLOAD_DIR, "alunos")
        os.makedirs(upload_dir_aluno, exist_ok=True)

        filename = f"{idUser}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagem.filename).suffix}"
        file_location = os.path.join(upload_dir_aluno, filename)

        conteudo = await imagem.read()
        with open(file_location, "wb") as buffer:
            buffer.write(conteudo)

        imagem_relativa = f"/static/uploads/alunos/{filename}"

    # Converter acesso_internet para booleano
    acesso_internet_bool = None
    if acesso_internet == "true":
        acesso_internet_bool = True
    elif acesso_internet == "false":
        acesso_internet_bool = False

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
        imagem=imagem_relativa,
        escola=escola,
        forma_ingresso=forma_ingresso,
        acesso_internet=acesso_internet_bool
    )

    return RedirectResponse(url="/login", status_code=303)

# --- Rota /perfil (AGORA REFATORADA) ---
@router.get("/perfil")
def perfil(
    request: Request,
    user_id: str = Depends(verificar_sessao),
    db: Session = Depends(get_db),
):
    """
    Exibe o perfil do aluno com dados e gráficos de desempenho.
    A lógica de coleta de dados é delegada ao AnalyticsService.
    """
    # user_id já foi validado pela dependência verificar_sessao
    # Converte user_id para int, pois o serviço espera int
    aluno_profile_data = AnalyticsService.get_aluno_profile_data(db, int(user_id))

    if not aluno_profile_data:
        # Se o serviço retornar None (aluno não encontrado apesar do user_id válido),
        # redireciona para o login ou uma página de erro.
        return RedirectResponse(url="/login?erro=aluno_nao_cadastrado", status_code=303)

    # Desempacota os dados retornados pelo serviço para passar ao template
    aluno = aluno_profile_data['aluno']
    materias = aluno_profile_data['materias']
    dados_grafico_pizza = aluno_profile_data['dados_grafico_pizza']
    dados_grafico_barra = aluno_profile_data['dados_grafico_barra']

    # Verifica formulários não respondidos e cria notificações
    NotificacaoDAO.verificar_formularios_nao_respondidos(db)

    # Busca todos os formulários e verifica quais o aluno ainda não respondeu
    formularios_pendentes = []
    todos_formularios = FormularioDAO.get_all(db)
    
    for form in todos_formularios:
        # Verifica se o aluno já respondeu este formulário
        ja_respondeu = RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, form.id)
        if not ja_respondeu:
            # Se o aluno não respondeu, adiciona à lista de pendências
            formularios_pendentes.append({
                "id": form.id,
                "titulo": form.titulo,
                "link": f"/formularios/{form.id}"
            })

    # Busca as notificações não lidas do aluno
    notificacoes = NotificacaoDAO.get_notificacoes_by_aluno(db, aluno.idAluno, lida=False)

    return templates.TemplateResponse(
        "aluno/perfil.html",
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
            "dados_grafico_pizza": dados_grafico_pizza,
            "dados_grafico_barra": dados_grafico_barra,
            "formularios_pendentes": formularios_pendentes,
            "notificacoes": notificacoes
        },
    )

# --- Rota /aluno/dashboard/{aluno_id} (AGORA REFATORADA) ---
@router.get("/aluno/dashboard/{aluno_id}", response_class=HTMLResponse)
async def dashboard_aluno(
    request: Request,
    aluno_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao) # Protege o dashboard do aluno
):
    """
    Exibe o dashboard detalhado de um aluno específico.
    A lógica de coleta de dados é delegada ao AnalyticsService.
    """
    # Embora a rota receba aluno_id, usamos user_id para garantir que o usuário logado
    # tenha permissão para ver este dashboard (se essa for a regra de negócio).
    # Caso contrário, se qualquer um puder ver o dashboard de qualquer aluno, remova user_id Depends(verificar_sessao).
    # Para simplicidade e consistência, a lógica aqui é para o aluno ver SEU PRÓPRIO dashboard.
    if int(user_id) != aluno_id and db.query(Usuario).filter(Usuario.id == int(user_id)).first().tipo != "gestor":
        # Se o ID na URL não corresponde ao usuário logado E o usuário não é gestor
        # Isso é uma regra de negócio, ajuste conforme a necessidade.
        raise HTTPException(
            status_code=403,
            detail="Acesso não autorizado ao dashboard de outro aluno.",
            headers={"Location": "/perfil"}, # Redireciona para o próprio perfil
        )

    # A lógica de busca de dados foi movida para o serviço
    dashboard_data = AnalyticsService.get_aluno_dashboard_data(db, aluno_id) # NOVO MÉTODO NO SERVIÇO

    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Dados do dashboard não encontrados para este aluno.")

    return templates.TemplateResponse(
        "aluno/dashboard_aluno.html",
        {
            "request": request,
            "aluno": dashboard_data['aluno'],
            "dados_disciplina": json.dumps(dashboard_data['dados_disciplina']),
            "dados_progressao": json.dumps(dashboard_data['dados_progressao'])
        }
    )

# --- Rotas /aluno/dados (mantidas, pois a lógica é de atualização direta) ---
@router.get("/aluno/dados")
def editar_dados_page(
    request: Request,
    user_id: str = Depends(verificar_sessao),
    db: Session = Depends(get_db)
):
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        "aluno/editar_dados.html",
        {
            "request": request,
            "aluno": aluno
        }
    )

@router.post("/aluno/dados")
async def editar_dados(
    request: Request,
    user_id: str = Depends(verificar_sessao),
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
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
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
        if aluno.imagem:
            caminho_antigo = aluno.imagem.lstrip('/')
            caminho_completo = os.path.join("templates", caminho_antigo)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                    print(f"Foto antiga removida: {caminho_completo}")
                except Exception as e:
                    print(f"Erro ao remover foto antiga: {e}")
        
        filename = f"aluno_{aluno.idAluno}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(foto.filename).suffix}"
        file_location = os.path.join(UPLOAD_DIR, "alunos", filename)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        
        conteudo = await foto.read()
        with open(file_location, "wb") as buffer:
            buffer.write(conteudo)
        
        aluno.imagem = f"/static/uploads/alunos/{filename}"
    
    db.commit()
    return RedirectResponse(url="/perfil", status_code=303)