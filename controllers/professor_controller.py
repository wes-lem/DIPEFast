import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from dao.database import get_db
from models.banco_questoes import BancoQuestoes
from models.prova import Prova
from models.prova_questao import ProvaQuestao
from models.prova_turma import ProvaTurma, StatusProvaTurma
from models.resultado import Resultado
from models.usuario import Usuario

from controllers.usuario_controller import verificar_sessao
from dao.professor_dao import ProfessorDAO
from dao.campus_dao import CampusDAO
from dao.turma_dao import TurmaDAO
from dao.aluno_turma_dao import AlunoTurmaDAO
from dao.banco_questoes_dao import BancoQuestoesDAO
from dao.prova_questao_dao import ProvaQuestaoDAO
from dao.notificacao_professor_dao import NotificacaoProfessorDAO

from app_config import templates
from services.relatorios_service import RelatorioService
from utils.export_service import pdf_response_from_html, docx_response_from_data

# Configurações
UPLOAD_DIR = Path("templates/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

def verificar_professor_sessao(request: Request, db: Session = Depends(get_db)):
    """
    Dependência para verificar se o usuário na sessão é um professor.
    """
    session_user_id = verificar_sessao(request)
    usuario = db.query(Usuario).filter(Usuario.id == int(session_user_id)).first()
    if not usuario or usuario.tipo != "professor":
        raise HTTPException(
            status_code=303,
            detail="Acesso não autorizado para professores",
            headers={"Location": "/login?erro=Acesso nao autorizado"},
        )
    return usuario.id

# === ROTAS DE CADASTRO DE PROFESSOR ===

@router.get("/professor/cadastrar")
def cadastro_professor_page(request: Request, db: Session = Depends(get_db)):
    """Página de cadastro público de professor"""
    campus = CampusDAO.get_all(db)
    return templates.TemplateResponse(
        "professor/cadastro_professor.html", 
        {"request": request, "campus": campus}
    )

@router.post("/professor/cadastrar")
async def cadastrar_professor(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    campus_id: int = Form(...),
    especialidade: str = Form(None),
    foto: UploadFile = File(None),
    foto_cortada: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Processa cadastro público de professor"""
    # Validações
    if senha != confirmar_senha:
        campus = CampusDAO.get_all(db)
        return templates.TemplateResponse(
            "professor/cadastro_professor.html",
            {"request": request, "campus": campus, "erro": "Senhas não coincidem"}
        )
    
    if len(senha) < 6:
        campus = CampusDAO.get_all(db)
        return templates.TemplateResponse(
            "professor/cadastro_professor.html",
            {"request": request, "campus": campus, "erro": "Senha deve ter pelo menos 6 caracteres"}
        )
    
    # Verificar se campus existe
    campus = CampusDAO.get_by_id(db, campus_id)
    if not campus:
        campus_list = CampusDAO.get_all(db)
        return templates.TemplateResponse(
            "professor/cadastro_professor.html",
            {"request": request, "campus": campus_list, "erro": "Campus inválido"}
        )
    
    # Processar upload de foto
    imagem_path = None
    professor_upload_dir = os.path.join(UPLOAD_DIR, "professores")
    os.makedirs(professor_upload_dir, exist_ok=True)
    # Prioriza base64 recortado
    if foto_cortada:
        try:
            import base64
            header, b64data = foto_cortada.split(",", 1) if "," in foto_cortada else ("", foto_cortada)
            img_bytes = base64.b64decode(b64data)
            filename = f"professor_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            file_location = os.path.join(professor_upload_dir, filename)
            with open(file_location, "wb") as f:
                f.write(img_bytes)
            imagem_path = f"/static/uploads/professores/{filename}"
        except Exception as e:
            print(f"Falha ao salvar foto cortada do professor: {e}")
    elif foto and foto.filename:
        filename = f"professor_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(foto.filename).suffix}"
        file_location = os.path.join(professor_upload_dir, filename)
        with open(file_location, "wb") as buffer:
            buffer.write(await foto.read())
        imagem_path = f"/static/uploads/professores/{filename}"
    
    # Criar professor
    professor = ProfessorDAO.create_with_usuario(
        db=db,
        email=email,
        senha=senha,
        nome=nome,
        campus_id=campus_id,
        especialidade=especialidade,
        imagem=imagem_path
    )
    
    if not professor:
        campus_list = CampusDAO.get_all(db)
        return templates.TemplateResponse(
            "professor/cadastro_professor.html",
            {"request": request, "campus": campus_list, "erro": "E-mail já cadastrado"}
        )
    
    return RedirectResponse(url="/login?sucesso=Professor cadastrado com sucesso", status_code=303)

# === ROTAS DO DASHBOARD DO PROFESSOR ===

@router.get("/professor/dashboard")
def dashboard_professor(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Dashboard do professor"""
    professor = ProfessorDAO.get_with_campus(db, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    
    # Buscar estatísticas
    turmas_count = len(TurmaDAO.get_active_by_professor(db, professor_id))
    questoes_count = BancoQuestoesDAO.get_count_by_professor(db, professor_id)
    provas_count = db.query(func.count(Prova.id)).filter(Prova.professor_id == professor_id).scalar()
    
    # Buscar turmas com contagem de alunos
    turmas_with_alunos = TurmaDAO.get_with_alunos_count(db, professor_id)
    
    # Buscar notificações não lidas
    notificacoes_count = NotificacaoProfessorDAO.get_unread_count(db, professor_id)
    
    # Buscar provas recentes
    provas_recentes = db.query(Prova).filter(
        Prova.professor_id == professor_id
    ).order_by(Prova.data_criacao.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        "professor/dashboard_professor.html",
        {
            "request": request,
            "professor": professor,
            "turmas_count": turmas_count,
            "questoes_count": questoes_count,
            "provas_count": provas_count,
            "turmas_with_alunos": turmas_with_alunos,
            "notificacoes_count": notificacoes_count,
            "provas_recentes": provas_recentes
        }
    )

# === RELATÓRIOS DO PROFESSOR ===
@router.get("/professor/relatorios")
def relatorios_professor(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    dados = RelatorioService.get_professor_report_data(db, professor_id)
    return templates.TemplateResponse(
        "professor/relatorios.html",
        {"request": request, "dados": dados}
    )

@router.get("/professor/relatorios/export/pdf")
def export_relatorios_professor_pdf(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    dados = RelatorioService.get_professor_report_data(db, professor_id)
    # Renderiza o HTML do template em string
    template = templates.get_template("professor/relatorios.html")
    html = template.render(request=request, dados=dados)
    return pdf_response_from_html(html, filename="relatorio_professor.pdf")

@router.get("/professor/relatorios/export/docx")
def export_relatorios_professor_docx(
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    dados = RelatorioService.get_professor_report_data(db, professor_id)
    sections = {
        "Provas (médias)": {"labels": dados["provas"]["labels"], "medias": dados["provas"]["medias"]},
        "Provas (participação)": {"labels": dados["provas"]["labels"], "medias": dados["provas"]["participacao"]},
        "Médias por Matéria": dados["materias"],
    }
    return docx_response_from_data("Relatório do Professor", sections, filename="relatorio_professor.docx")

# === ROTAS DE TURMAS ===

@router.get("/professor/turmas")
def turmas_professor(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Lista turmas do professor"""
    turmas = TurmaDAO.get_by_professor(db, professor_id)
    return templates.TemplateResponse(
        "professor/turmas.html",
        {"request": request, "turmas": turmas}
    )

@router.get("/professor/turmas/criar")
def criar_turma_page(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para criar nova turma"""
    professor = ProfessorDAO.get_with_campus(db, professor_id)
    return templates.TemplateResponse(
        "professor/criar_turma.html",
        {"request": request, "professor": professor}
    )

@router.post("/professor/turmas/criar")
def criar_turma(
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Cria nova turma"""
    professor = ProfessorDAO.get_by_id(db, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    
    turma = TurmaDAO.create(
        db=db,
        nome=nome,
        professor_id=professor_id,
        campus_id=professor.campus_id
    )
    
    # Criar notificação
    NotificacaoProfessorDAO.create_turma_criada_notification(
        db=db,
        professor_id=professor_id,
        turma_nome=turma.nome,
        codigo=turma.codigo
    )
    
    return RedirectResponse(url="/professor/turmas", status_code=303)

@router.get("/professor/turmas/{turma_id}")
def gerenciar_turma(
    request: Request,
    turma_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Gerencia uma turma específica"""
    turma = TurmaDAO.get_by_id(db, turma_id)
    if not turma or turma.professor_id != professor_id:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    # Buscar alunos da turma
    alunos_turma = AlunoTurmaDAO.get_alunos_with_details_by_turma(db, turma_id)
    
    return templates.TemplateResponse(
        "professor/gerenciar_turma.html",
        {
            "request": request,
            "turma": turma,
            "alunos_turma": alunos_turma
        }
    )

@router.post("/professor/turmas/{turma_id}/arquivar")
def arquivar_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Arquiva uma turma"""
    turma = TurmaDAO.get_by_id(db, turma_id)
    if not turma or turma.professor_id != professor_id:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    TurmaDAO.archive(db, turma_id)
    return RedirectResponse(url="/professor/turmas", status_code=303)

@router.post("/professor/turmas/{turma_id}/ativar")
def ativar_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Ativa uma turma arquivada"""
    turma = TurmaDAO.get_by_id(db, turma_id)
    if not turma or turma.professor_id != professor_id:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    TurmaDAO.activate(db, turma_id)
    return RedirectResponse(url="/professor/turmas", status_code=303)

@router.post("/professor/turmas/{turma_id}/excluir")
def excluir_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Exclui uma turma permanentemente"""
    turma = TurmaDAO.get_by_id(db, turma_id)
    if not turma or turma.professor_id != professor_id:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    TurmaDAO.delete(db, turma_id)
    return RedirectResponse(url="/professor/turmas", status_code=303)

# === ROTAS DE BANCO DE QUESTÕES ===

@router.get("/professor/banco-questoes")
def banco_questoes(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao),
    search: Optional[str] = Query(None),
    materia: Optional[str] = Query(None)
):
    """Lista questões do banco do professor"""
    questoes = BancoQuestoesDAO.search_questoes(db, professor_id, search, materia)
    materias = BancoQuestoesDAO.get_materias_by_professor(db, professor_id)
    
    return templates.TemplateResponse(
        "professor/banco_questoes.html",
        {
            "request": request,
            "questoes": questoes,
            "materias": materias,
            "search": search,
            "materia_selected": materia
        }
    )

@router.get("/professor/banco-questoes/criar")
def criar_questao_page(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para criar nova questão"""
    return templates.TemplateResponse(
        "professor/criar_questao.html",
        {"request": request}
    )

@router.post("/professor/banco-questoes/criar")
async def criar_questao(
    request: Request,
    enunciado: str = Form(...),
    opcao_a: str = Form(...),
    opcao_b: str = Form(...),
    opcao_c: str = Form(...),
    opcao_d: str = Form(...),
    opcao_e: str = Form(...),
    resposta_correta: str = Form(...),
    materia: str = Form(...),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Cria nova questão no banco"""
    # Processar upload de imagem
    imagem_path = None
    if imagem and imagem.filename:
        questoes_upload_dir = os.path.join(UPLOAD_DIR, "questoes")
        os.makedirs(questoes_upload_dir, exist_ok=True)
        filename = f"questao_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagem.filename).suffix}"
        file_location = os.path.join(questoes_upload_dir, filename)
        
        with open(file_location, "wb") as buffer:
            buffer.write(await imagem.read())
        imagem_path = f"/static/uploads/questoes/{filename}"
    
    BancoQuestoesDAO.create(
        db=db,
        professor_id=professor_id,
        enunciado=enunciado,
        opcao_a=opcao_a,
        opcao_b=opcao_b,
        opcao_c=opcao_c,
        opcao_d=opcao_d,
        opcao_e=opcao_e,
        resposta_correta=resposta_correta,
        materia=materia,
        imagem=imagem_path
    )
    
    return RedirectResponse(url="/professor/banco-questoes", status_code=303)

# === ROTAS DE PROVAS ===

@router.get("/professor/provas")
def provas_professor(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Lista provas do professor com informações de alunos que responderam"""
    from sqlalchemy.orm import joinedload
    
    # Buscar provas com contagem de resultados
    provas = db.query(Prova).options(
        joinedload(Prova.resultados).joinedload(Resultado.aluno)
    ).filter(Prova.professor_id == professor_id).order_by(Prova.data_criacao.desc()).all()
    
    # Para cada prova, calcular quantos alunos responderam
    for prova in provas:
        prova.alunos_responderam = len(prova.resultados)
        if prova.resultados:
            prova.nota_media = sum(r.acertos for r in prova.resultados) / len(prova.resultados)
        else:
            prova.nota_media = 0
    
    return templates.TemplateResponse(
        "professor/provas.html",
        {"request": request, "provas": provas}
    )

@router.get("/professor/provas/criar")
def criar_prova_page(
    request: Request,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para criar nova prova"""
    questoes = BancoQuestoesDAO.get_active_by_professor(db, professor_id)
    return templates.TemplateResponse(
        "professor/criar_prova.html",
        {"request": request, "questoes": questoes}
    )

@router.post("/professor/provas/criar")
def criar_prova(
    request: Request,
    titulo: str = Form(...),
    materia: str = Form(...),
    questoes_selecionadas: List[int] = Form(...),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Cria nova prova"""
    # Criar prova
    prova = Prova(
        titulo=titulo,
        materia=materia,
        professor_id=professor_id,
        status="rascunho"
    )
    db.add(prova)
    db.commit()
    db.refresh(prova)
    
    # Adicionar questões à prova
    for i, questao_id in enumerate(questoes_selecionadas, 1):
        ProvaQuestaoDAO.create(db, prova.id, questao_id, i)
    
    # Criar notificação
    NotificacaoProfessorDAO.create_prova_criada_notification(
        db=db,
        professor_id=professor_id,
        prova_titulo=prova.titulo
    )
    
    return RedirectResponse(url="/professor/provas", status_code=303)

# === ROTAS DE NOTIFICAÇÕES ===

@router.get("/professor/notificacoes", name="notificacoes_professor")
def notificacoes_professor(
    request: Request,
    filtro: str = "todas",
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Lista notificações do professor com base em um filtro"""
    if filtro == "nao_lidas":
        notificacoes = NotificacaoProfessorDAO.get_unread_by_professor(db, professor_id)
    elif filtro == "lidas":
        notificacoes = NotificacaoProfessorDAO.get_read_by_professor(db, professor_id)
    else:
        notificacoes = NotificacaoProfessorDAO.get_by_professor(db, professor_id)
    
    # Pegamos a contagem de não lidas para o badge
    nao_lidas_count = NotificacaoProfessorDAO.get_unread_count(db, professor_id)

    return templates.TemplateResponse(
        "professor/notificacoes.html",
        {
            "request": request, 
            "notificacoes": notificacoes,
            "nao_lidas_count": nao_lidas_count,
            "filtro_ativo": filtro  # Para saber qual aba marcar como ativa
        }
    )

# Rota NOVA para excluir uma notificação
@router.post("/professor/notificacoes/{notificacao_id}/excluir")
def excluir_notificacao(
    notificacao_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao) # Garante que o prof está logado
):
    """Exclui uma notificação específica"""
    # Adicionar lógica de permissão aqui se necessário
    NotificacaoProfessorDAO.delete(db, notificacao_id)
    return RedirectResponse(url="/professor/notificacoes", status_code=303)


# Rota NOVA para limpar (excluir) notificações lidas
@router.post("/professor/notificacoes/limpar-lidas")
def limpar_notificacoes_lidas(
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Exclui todas as notificações já lidas do professor"""
    NotificacaoProfessorDAO.delete_read_by_professor(db, professor_id)
    return RedirectResponse(url="/professor/notificacoes", status_code=303)


@router.post("/professor/notificacoes/{notificacao_id}/marcar-lida")
def marcar_notificacao_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Marca uma notificação como lida"""
    NotificacaoProfessorDAO.mark_as_read(db, notificacao_id)
    return RedirectResponse(url="/professor/notificacoes", status_code=303)

@router.post("/professor/notificacoes/marcar-todas-lidas")
def marcar_todas_notificacoes_lidas(
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Marca todas as notificações como lidas"""
    NotificacaoProfessorDAO.mark_all_as_read(db, professor_id)
    return RedirectResponse(url="/professor/notificacoes", status_code=303)

# === ROTAS DE GERENCIAMENTO DE PROVAS ===

@router.get("/professor/prova/{prova_id}/visualizar")
def visualizar_prova_professor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Visualiza uma prova específica do professor com alunos que responderam"""
    from sqlalchemy.orm import joinedload
    prova = db.query(Prova).options(
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco),
        joinedload(Prova.prova_turmas).joinedload(ProvaTurma.turma),
        joinedload(Prova.resultados).joinedload(Resultado.aluno)
    ).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Calcular estatísticas
    prova.alunos_responderam = len(prova.resultados)
    if prova.resultados:
        prova.nota_media = sum(r.acertos for r in prova.resultados) / len(prova.resultados)
        prova.maior_nota = max(r.acertos for r in prova.resultados)
        prova.menor_nota = min(r.acertos for r in prova.resultados)
    else:
        prova.nota_media = 0
        prova.maior_nota = 0
        prova.menor_nota = 0
    
    return templates.TemplateResponse(
        "professor/visualizar_prova.html",
        {"request": request, "prova": prova}
    )

@router.get("/professor/prova/{prova_id}/editar")
def editar_prova_professor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para editar uma prova"""
    from sqlalchemy.orm import joinedload
    prova = db.query(Prova).options(
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco)
    ).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Buscar questões do banco do professor
    questoes_banco = BancoQuestoesDAO.get_by_professor(db, professor_id)
    
    # Criar lista de IDs das questões já adicionadas à prova
    questoes_ja_adicionadas = [pq.questao_banco_id for pq in prova.prova_questoes]
    
    return templates.TemplateResponse(
        "professor/editar_prova.html",
        {"request": request, "prova": prova, "questoes_banco": questoes_banco, "questoes_ja_adicionadas": questoes_ja_adicionadas}
    )

@router.post("/professor/prova/{prova_id}/editar")
def salvar_edicao_prova(
    request: Request,
    prova_id: int,
    titulo: str = Form(...),
    materia: str = Form(...),
    questoes_selecionadas: List[int] = Form(...),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Salva as edições de uma prova"""
    prova = db.query(Prova).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Atualizar dados da prova
    prova.titulo = titulo
    prova.materia = materia
    
    # Remover questões antigas
    db.query(ProvaQuestao).filter(ProvaQuestao.prova_id == prova_id).delete()
    
    # Adicionar novas questões
    for i, questao_id in enumerate(questoes_selecionadas, 1):
        prova_questao = ProvaQuestao(
            prova_id=prova_id,
            questao_banco_id=questao_id,
            ordem=i
        )
        db.add(prova_questao)
    
    db.commit()
    return RedirectResponse(url="/professor/provas", status_code=303)

@router.post("/professor/prova-turma/{prova_turma_id}/editar-data")
def editar_data_expiracao_prova_turma(
    request: Request,
    prova_turma_id: int,
    data_expiracao: str = Form(...),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Edita a data de expiração de uma prova disponibilizada para uma turma"""
    from models.prova_turma import ProvaTurma
    from datetime import datetime
    
    # Buscar a prova_turma
    prova_turma = db.query(ProvaTurma).filter(
        ProvaTurma.id == prova_turma_id,
        ProvaTurma.professor_id == professor_id
    ).first()
    
    if not prova_turma:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Converter string para datetime
    try:
        nova_data = datetime.strptime(data_expiracao, "%Y-%m-%dT%H:%M")
        prova_turma.data_expiracao = nova_data
        db.commit()
        
        return {"success": True, "message": "Data de expiração atualizada com sucesso"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar data: {str(e)}")

@router.get("/professor/prova/{prova_id}/disponibilizar")
def disponibilizar_prova_professor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para disponibilizar uma prova para turmas"""
    from sqlalchemy.orm import joinedload
    prova = db.query(Prova).options(
        joinedload(Prova.prova_questoes)
    ).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Buscar turmas do professor
    turmas = TurmaDAO.get_active_by_professor(db, professor_id)
    
    return templates.TemplateResponse(
        "professor/disponibilizar_prova.html",
        {"request": request, "prova": prova, "turmas": turmas}
    )

@router.post("/professor/prova/{prova_id}/disponibilizar")
def salvar_disponibilizacao_prova(
    request: Request,
    prova_id: int,
    turmas_selecionadas: List[int] = Form(...),
    data_inicio: str = Form(...),
    data_expiracao: str = Form(...),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Salva a disponibilização de uma prova para turmas"""
    prova = db.query(Prova).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Converter strings para datetime
    from datetime import datetime
    data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%dT%H:%M")
    data_expiracao_dt = datetime.strptime(data_expiracao, "%Y-%m-%dT%H:%M")
    
    # Criar ProvaTurma para cada turma selecionada
    for turma_id in turmas_selecionadas:
        prova_turma = ProvaTurma(
            prova_id=prova_id,
            turma_id=turma_id,
            professor_id=professor_id,
            data_inicio=data_inicio_dt,
            data_expiracao=data_expiracao_dt,
            status=StatusProvaTurma.ATIVA
        )
        db.add(prova_turma)
    
    # Atualizar status da prova
    prova.status = "ativa"
    
    db.commit()
    return RedirectResponse(url="/professor/provas", status_code=303)

@router.post("/professor/prova/{prova_id}/excluir")
def excluir_prova_professor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Exclui uma prova do professor"""
    prova = db.query(Prova).filter(Prova.id == prova_id, Prova.professor_id == professor_id).first()
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Verificar se a prova pode ser excluída (não pode ter respostas)
    # Implementar verificação se necessário
    
    db.delete(prova)
    db.commit()
    return RedirectResponse(url="/professor/provas", status_code=303)

# === ROTAS DE GERENCIAMENTO DE QUESTÕES ===

@router.get("/professor/questao/{questao_id}/visualizar")
def visualizar_questao_professor(
    request: Request,
    questao_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Visualiza uma questão específica do professor"""
    questao = db.query(BancoQuestoes).filter(
        BancoQuestoes.id == questao_id, 
        BancoQuestoes.professor_id == professor_id
    ).first()
    
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    
    return templates.TemplateResponse(
        "professor/visualizar_questao.html",
        {"request": request, "questao": questao}
    )

@router.get("/professor/questao/{questao_id}/editar")
def editar_questao_professor(
    request: Request,
    questao_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Página para editar uma questão"""
    questao = db.query(BancoQuestoes).filter(
        BancoQuestoes.id == questao_id, 
        BancoQuestoes.professor_id == professor_id
    ).first()
    
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    
    return templates.TemplateResponse(
        "professor/editar_questao.html",
        {"request": request, "questao": questao}
    )

@router.post("/professor/questao/{questao_id}/editar")
def salvar_edicao_questao(
    request: Request,
    questao_id: int,
    enunciado: str = Form(...),
    opcao_a: str = Form(...),
    opcao_b: str = Form(...),
    opcao_c: str = Form(...),
    opcao_d: str = Form(...),
    opcao_e: str = Form(...),
    resposta_correta: str = Form(...),
    materia: str = Form(...),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Salva as edições de uma questão"""
    questao = db.query(BancoQuestoes).filter(
        BancoQuestoes.id == questao_id, 
        BancoQuestoes.professor_id == professor_id
    ).first()
    
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    
    # Atualizar dados da questão
    questao.enunciado = enunciado
    questao.opcao_a = opcao_a
    questao.opcao_b = opcao_b
    questao.opcao_c = opcao_c
    questao.opcao_d = opcao_d
    questao.opcao_e = opcao_e
    questao.resposta_correta = resposta_correta
    questao.materia = materia
    
    # Processar upload de imagem se fornecido
    if imagem and imagem.filename:
        # Remover imagem antiga se existir
        if questao.imagem:
            caminho_antigo = questao.imagem.replace("/static/uploads/", "")
            caminho_completo = os.path.join("templates", caminho_antigo)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except Exception as e:
                    print(f"Erro ao remover imagem antiga: {e}")
        
        # Salvar nova imagem
        questao_upload_dir = os.path.join(UPLOAD_DIR, "questoes")
        os.makedirs(questao_upload_dir, exist_ok=True)
        filename = f"questao_{questao_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagem.filename).suffix}"
        file_location = os.path.join(questao_upload_dir, filename)
        
        with open(file_location, "wb") as buffer:
            buffer.write(imagem.file.read())
        questao.imagem = f"/static/uploads/questoes/{filename}"
    
    db.commit()
    return RedirectResponse(url="/professor/banco-questoes", status_code=303)

@router.post("/professor/questao/{questao_id}/excluir")
def excluir_questao_professor(
    request: Request,
    questao_id: int,
    db: Session = Depends(get_db),
    professor_id: int = Depends(verificar_professor_sessao)
):
    """Exclui uma questão do professor"""
    questao = db.query(BancoQuestoes).filter(
        BancoQuestoes.id == questao_id, 
        BancoQuestoes.professor_id == professor_id
    ).first()
    
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    
    # Verificar se a questão está sendo usada em alguma prova
    # Implementar verificação se necessário
    
    # Remover imagem se existir
    if questao.imagem:
        caminho_imagem = questao.imagem.replace("/static/uploads/", "")
        caminho_completo = os.path.join("templates", caminho_imagem)
        if os.path.exists(caminho_completo):
            try:
                os.remove(caminho_completo)
            except Exception as e:
                print(f"Erro ao remover imagem: {e}")
    
    db.delete(questao)
    db.commit()
    return RedirectResponse(url="/professor/banco-questoes", status_code=303)
