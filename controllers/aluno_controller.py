import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from dao.database import get_db
from dao.aluno_dao import AlunoDAO
from dao.usuario_dao import UsuarioDAO
from dao.turma_dao import TurmaDAO
from dao.aluno_turma_dao import AlunoTurmaDAO
from dao.prova_turma_dao import ProvaTurmaDAO
from models.aluno import Aluno
from models.usuario import Usuario
from models.turma import Turma
from models.prova import Prova
from models.prova_questao import ProvaQuestao
from models.resposta import Resposta
from models.resultado import Resultado

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
    observacoes: Optional[str] = Form(None),
    imagem: UploadFile = File(None),
    imagem_cortada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == idUser).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if curso not in ["Redes de Computadores", "Agropecuária", "Partiu IF"]:
        raise HTTPException(status_code=400, detail="Curso inválido")

    imagem_relativa = None
    upload_dir_aluno = os.path.join(UPLOAD_DIR, "alunos")
    os.makedirs(upload_dir_aluno, exist_ok=True)

    # Se veio imagem cortada em base64, prioriza e salva como jpg
    if imagem_cortada:
        try:
            import base64
            header, b64data = imagem_cortada.split(",", 1) if "," in imagem_cortada else ("", imagem_cortada)
            img_bytes = base64.b64decode(b64data)
            filename = f"{idUser}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            file_location = os.path.join(upload_dir_aluno, filename)
            with open(file_location, "wb") as f:
                f.write(img_bytes)
            imagem_relativa = f"/static/uploads/alunos/{filename}"
        except Exception as e:
            print(f"Falha ao salvar imagem cortada: {e}")
            # fallback para arquivo bruto se existir

    # Caso não tenha imagem_cortada válida, usa o arquivo original (sem crop)
    if not imagem_relativa and imagem and imagem.filename:
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
        acesso_internet=acesso_internet_bool,
        observacoes=observacoes
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

    max_chart_value = aluno_profile_data.get('maxChartValue', 10)

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
            "aluno": aluno,
            "id": aluno.idAluno,
            "nome": aluno.nome,
            "imagem": aluno.imagem,
            "idade": aluno.idade,
            "municipio": aluno.municipio,
            "ano": aluno.ano,
            "curso": aluno.curso,
            "materias": materias,
            "provas_turmas": aluno_profile_data.get('provas_turmas', []),
            "dados_grafico_pizza": dados_grafico_pizza,
            "dados_grafico_barra": dados_grafico_barra,
            "maxChartValue": max_chart_value,
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
    escola: Optional[str] = Form(None),
    forma_ingresso: Optional[str] = Form(None),
    acesso_internet: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    foto: UploadFile = File(None),
    foto_cortada: Optional[str] = Form(None),
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
    aluno.escola = escola
    aluno.forma_ingresso = forma_ingresso
    if acesso_internet == "true":
        aluno.acesso_internet = True
    elif acesso_internet == "false":
        aluno.acesso_internet = False
    else:
        aluno.acesso_internet = None
    aluno.observacoes = observacoes
    
    # Atualizar foto se fornecida (prioriza base64 cortada)
    if foto_cortada or (foto and foto.filename):
        # Remover antiga se existir
        if aluno.imagem:
            caminho_antigo = aluno.imagem.lstrip('/')
            caminho_completo = os.path.join("templates", caminho_antigo)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except Exception as e:
                    print(f"Erro ao remover foto antiga: {e}")

        upload_dir_aluno = os.path.join(UPLOAD_DIR, "alunos")
        os.makedirs(upload_dir_aluno, exist_ok=True)

        if foto_cortada:
            try:
                import base64
                header, b64data = foto_cortada.split(",", 1) if "," in foto_cortada else ("", foto_cortada)
                img_bytes = base64.b64decode(b64data)
                filename = f"aluno_{aluno.idAluno}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                file_location = os.path.join(upload_dir_aluno, filename)
                with open(file_location, "wb") as f:
                    f.write(img_bytes)
                aluno.imagem = f"/static/uploads/alunos/{filename}"
            except Exception as e:
                print(f"Falha ao salvar foto cortada: {e}")
        elif foto and foto.filename:
            filename = f"aluno_{aluno.idAluno}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(foto.filename).suffix}"
            file_location = os.path.join(upload_dir_aluno, filename)
            conteudo = await foto.read()
            with open(file_location, "wb") as buffer:
                buffer.write(conteudo)
            aluno.imagem = f"/static/uploads/alunos/{filename}"
    
    db.commit()
    return RedirectResponse(url="/perfil", status_code=303)

# === ROTAS DE TURMAS PARA ALUNOS ===

@router.get("/aluno/turmas")
def turmas_aluno(
    request: Request,
    sucesso: str = None,
    erro: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Lista turmas do aluno"""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    turmas_aluno = AlunoTurmaDAO.get_turmas_with_details_by_aluno(db, aluno.idAluno)
    return templates.TemplateResponse(
        "aluno/turmas_aluno.html",
        {
            "request": request, 
            "turmas_aluno": turmas_aluno, 
            "aluno": aluno,
            "sucesso": sucesso,
            "erro": erro
        }
    )


@router.post("/aluno/turmas/entrar")
def entrar_turma(
    request: Request,
    codigo: str = Form(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Processa entrada do aluno em turma"""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Buscar turma pelo código
    turma = TurmaDAO.get_by_codigo(db, codigo.upper())
    if not turma:
        return RedirectResponse(url="/aluno/turmas?erro=Código de turma inválido", status_code=303)
    
    # Verificar se aluno já está na turma
    if AlunoTurmaDAO.is_aluno_in_turma(db, aluno.idAluno, turma.id):
        return RedirectResponse(url="/aluno/turmas?erro=Você já está matriculado nesta turma", status_code=303)
    
    # Adicionar aluno à turma
    aluno_turma = AlunoTurmaDAO.create(db, aluno.idAluno, turma.id)
    if aluno_turma:
        return RedirectResponse(url="/aluno/turmas?sucesso=Entrou na turma com sucesso", status_code=303)
    else:
        return RedirectResponse(url="/aluno/turmas?erro=Erro ao entrar na turma", status_code=303)

@router.get("/aluno/provas")
def provas_aluno(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Lista provas disponíveis para o aluno"""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    ProvaTurmaDAO.check_and_update_expired(db)
    
    # Buscar provas ativas das turmas do aluno
    provas_ativas = ProvaTurmaDAO.get_provas_for_aluno(db, aluno.idAluno)
    
    # Buscar provas expiradas para consulta
    provas_expiradas = ProvaTurmaDAO.get_provas_expired_for_aluno(db, aluno.idAluno)
    
    # Para cada prova, verificar se o aluno já respondeu
    for prova_turma in provas_ativas:
        resultado = db.query(Resultado).filter(
            Resultado.aluno_id == aluno.idAluno,
            Resultado.prova_id == prova_turma.prova.id
        ).first()
        prova_turma.aluno_ja_respondeu = resultado is not None
        if resultado:
            prova_turma.resultado_aluno = resultado
    
    for prova_turma in provas_expiradas:
        resultado = db.query(Resultado).filter(
            Resultado.aluno_id == aluno.idAluno,
            Resultado.prova_id == prova_turma.prova.id
        ).first()
        prova_turma.aluno_ja_respondeu = resultado is not None
        if resultado:
            prova_turma.resultado_aluno = resultado
    
    return templates.TemplateResponse(
        "aluno/provas_aluno.html",
        {
            "request": request, 
            "aluno": aluno,
            "provas_ativas": provas_ativas,
            "provas_expiradas": provas_expiradas
        }
    )

# === ROTAS DE DETALHES PARA ALUNO ===

@router.get("/aluno/turma/{turma_id}/detalhes")
def detalhes_turma_aluno(
    request: Request,
    turma_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Detalhes de uma turma específica para o aluno"""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verificar se o aluno está na turma
    if not AlunoTurmaDAO.is_aluno_in_turma(db, aluno.idAluno, turma_id):
        raise HTTPException(status_code=403, detail="Você não está matriculado nesta turma")
    
    turma = TurmaDAO.get_with_details(db, turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    # Buscar alunos da turma (colegas)
    colegas = AlunoTurmaDAO.get_alunos_with_details_by_turma(db, turma_id)
    
    # Buscar provas da turma
    provas_turma = ProvaTurmaDAO.get_by_turma(db, turma_id)
    
    return templates.TemplateResponse(
        "aluno/detalhes_turma.html",
        {
            "request": request, 
            "turma": turma, 
            "aluno": aluno,
            "colegas": colegas,
            "provas_turma": provas_turma
        }
    )

@router.get("/aluno/prova/{prova_id}/responder")
def responder_prova_aluno(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Página para o aluno responder uma prova"""
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    ProvaTurmaDAO.check_and_update_expired(db)
    
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Buscar prova com dados relacionados
    from sqlalchemy.orm import joinedload
    prova = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Verificar se o aluno pode responder a prova
    # (implementar lógica de verificação de turma e prazo)
    
    return templates.TemplateResponse(
        "aluno/responder_prova.html",
        {"request": request, "prova": prova, "aluno": aluno}
    )

@router.post("/aluno/prova/{prova_id}/responder")
async def salvar_resposta_prova(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    """Salva as respostas do aluno para uma prova"""
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    ProvaTurmaDAO.check_and_update_expired(db)
    
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Buscar prova
    from sqlalchemy.orm import joinedload
    prova = db.query(Prova).options(
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Verificar se o aluno já respondeu esta prova
    resultado_existente = db.query(Resultado).filter(
        Resultado.aluno_id == aluno.idAluno,
        Resultado.prova_id == prova_id
    ).first()
    
    if resultado_existente:
        return RedirectResponse(url="/aluno/provas?erro=Você já respondeu esta prova", status_code=303)
    
    # Processar respostas do formulário
    form_data = await request.form()
    respostas_corretas = 0
    total_questoes = len(prova.prova_questoes)
    
    # Salvar cada resposta
    for questao_prova in prova.prova_questoes:
        questao_id = questao_prova.questao_banco.id
        resposta_aluno = form_data.get(f"questao_{questao_id}")
        
        if resposta_aluno:
            # Verificar se já existe uma resposta para esta questão (evitar duplicatas)
            resposta_existente = db.query(Resposta).filter(
                Resposta.aluno_id == aluno.idAluno,
                Resposta.questao_id == questao_id
            ).first()
            
            if resposta_existente:
                # Atualizar resposta existente
                resposta_existente.resposta = resposta_aluno
            else:
                # Criar nova resposta
                resposta = Resposta(
                    aluno_id=aluno.idAluno,
                    questao_id=questao_id,
                    resposta=resposta_aluno
                )
                db.add(resposta)
            
            # Verificar se está correta
            if resposta_aluno == questao_prova.questao_banco.resposta_correta:
                respostas_corretas += 1
    
    # Calcular nota e situação
    total_questoes = len(prova.prova_questoes)
    from utils.nota_service import calcular_nota_e_situacao
    nota, situacao = calcular_nota_e_situacao(respostas_corretas, total_questoes)
    
    resultado = Resultado(
        aluno_id=aluno.idAluno,
        prova_id=prova_id,
        acertos=respostas_corretas,
        situacao=situacao,
        nota=nota,
        total_questoes=total_questoes
    )
    db.add(resultado)
    
    db.commit()
    
    return RedirectResponse(url="/aluno/provas?sucesso=Prova respondida com sucesso!", status_code=303)

@router.get("/aluno/prova/{prova_id}/consultar")
def consultar_prova_aluno(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(verificar_sessao)
):
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    ProvaTurmaDAO.check_and_update_expired(db)
    """Página para o aluno consultar uma prova (expirada ou já respondida)"""
    aluno = db.query(Aluno).filter(Aluno.idUser == int(user_id)).first()
    if not aluno:
        return RedirectResponse(url="/login", status_code=303)
    
    # Buscar prova com dados relacionados
    from sqlalchemy.orm import joinedload
    from models.prova_turma import ProvaTurma
    from models.resposta import Resposta
    from models.resultado import Resultado
    from datetime import datetime
    
    prova = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Verificar se o aluno já respondeu a prova
    resultado = db.query(Resultado).filter(
        Resultado.aluno_id == aluno.idAluno,
        Resultado.prova_id == prova_id
    ).first()
    
    # Buscar as respostas do aluno para esta prova
    # Usando uma subquery para pegar apenas a resposta mais recente de cada questão
    from sqlalchemy import func
    subq = db.query(
        Resposta.questao_id,
        func.max(Resposta.id).label('max_id')
    ).filter(
        Resposta.aluno_id == aluno.idAluno,
        Resposta.questao_id.in_([pq.questao_banco_id for pq in prova.prova_questoes])
    ).group_by(Resposta.questao_id).subquery()
    
    respostas_aluno = db.query(Resposta).join(
        subq,
        (Resposta.questao_id == subq.c.questao_id) & (Resposta.id == subq.c.max_id)
    ).all()
    
    # Determinar o status da prova
    prova_turma = db.query(ProvaTurma).filter(
        ProvaTurma.prova_id == prova_id
    ).first()
    
    agora = datetime.now()
    is_expirada = prova_turma and prova_turma.data_expiracao < agora
    is_respondida = resultado is not None
    
    # Determinar status para exibição
    if is_respondida and not is_expirada:
        status_prova = "respondida"
        status_texto = "Prova Respondida"
        status_cor = "success"
    elif is_respondida and is_expirada:
        status_prova = "respondida_expirada"
        status_texto = "Prova Respondida (Expirada)"
        status_cor = "info"
    elif is_expirada:
        status_prova = "expirada"
        status_texto = "Prova Expirada"
        status_cor = "warning"
    else:
        status_prova = "ativa"
        status_texto = "Prova Ativa"
        status_cor = "primary"
    
    return templates.TemplateResponse(
        "aluno/consultar_prova.html",
        {
            "request": request, 
            "prova": prova, 
            "aluno": aluno,
            "resultado": resultado,
            "respostas_aluno": respostas_aluno,
            "status_prova": status_prova,
            "status_texto": status_texto,
            "status_cor": status_cor,
            "is_expirada": is_expirada,
            "is_respondida": is_respondida
        }
    )