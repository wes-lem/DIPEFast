import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func
from passlib.hash import bcrypt

# Importações dos seus DAOs e Models
from dao.database import get_db
from models.aluno import Aluno
from models.gestor import Gestor
from models.prova import Prova
from models.questao import Questao
from models.resposta import Resposta
from models.resultado import Resultado
from models.usuario import Usuario
from models.notificacao import Notificacao
from models.professor import Professor
from models.campus import Campus
from models.turma import Turma
from models.banco_questoes import BancoQuestoes
from models.prova_questao import ProvaQuestao
from models.prova_turma import ProvaTurma
from models.resposta_formulario import RespostaFormulario
from models.pergunta_formulario import PerguntaFormulario

from controllers.usuario_controller import verificar_sessao

from services.graficos_service import AnalyticsService

from dao.resposta_formulario_dao import RespostaFormularioDAO
from dao.professor_dao import ProfessorDAO
from dao.campus_dao import CampusDAO
from dao.turma_dao import TurmaDAO
from dao.aluno_turma_dao import AlunoTurmaDAO
from dao.prova_turma_dao import ProvaTurmaDAO

from utils.auth import verificar_gestor_sessao

# Importar a instância templates do app_config
from app_config import templates
from services.relatorios_service import RelatorioService
from utils.export_service import pdf_response_from_html, docx_response_from_data

def verificar_gestor_sessao(request: Request, db: Session = Depends(get_db)):
    """
    Dependência para verificar se o usuário na sessão é um gestor.
    Redireciona para a página de login se não for.
    """
    session_user_id = verificar_sessao(request)
    usuario = db.query(Usuario).filter(Usuario.id == int(session_user_id)).first()
    if not usuario or usuario.tipo != "gestor":
        raise HTTPException(
            status_code=303,
            detail="Acesso não autorizado para gestores",
            headers={"Location": "/login?erro=Acesso nao autorizado"},
        )
    return usuario.id

# --- Configurações Iniciais ---
UPLOAD_DIR = Path("templates/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

# --- Funções Auxiliares (mantidas, mas podem ser movidas para um utilitário se usadas em mais lugares) ---
async def salvar_imagem(imagem: UploadFile, nome_arquivo: str):
    """Salva uma imagem no diretório de uploads e retorna o caminho relativo."""
    upload_path = os.path.join(UPLOAD_DIR, "provas", nome_arquivo)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    with open(upload_path, "wb") as buffer:
        buffer.write(await imagem.read())
    return f"/static/uploads/provas/{nome_arquivo}"

# --- Rotas de Gerenciamento de Provas ---
@router.get("/provas/cadastrar")
def cadastro_prova_page(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe a página de cadastro de provas e lista as provas existentes."""
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    
    provas = db.query(Prova).all()
    provas_info = []
    
    for prova in provas:
        questoes = db.query(Questao).filter(Questao.prova_id == prova.id).all()
        materia = prova.materia.strip()
        # Não é ideal corrigir codificação aqui, mas mantido como estava
        materia = materia.replace('\u00eas', 'ês') 
        provas_info.append({
            'id': prova.id,
            'materia': materia,
            'data_criacao': prova.data_criacao.strftime('%d/%m/%Y'),
            'questoes': len(questoes)
        })
    
    print("Provas encontradas:", provas_info) # Debug
    
    return templates.TemplateResponse(
        "gestor/cadastro_prova.html", 
        {
            "request": request,
            "provas_info": provas_info
        }
    )

@router.post("/provas/cadastrar")
async def cadastrar_prova(
    request: Request,
    materia: str = Form(...),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao), # Protegido por gestor
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
    """Rota para cadastrar uma prova e suas 15 questões."""
    print("📌 Dados do formulário recebidos:", dict(await request.form())) # Debug, usar await aqui

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

    for i in range(15):
        image_path = None
        if imagens and i < len(imagens) and imagens[i] and imagens[i].filename: # Adicionado 'i < len(imagens)' para segurança
            filename = f"questao_{nova_prova.id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagens[i].filename).suffix}"
            image_path = await salvar_imagem(imagens[i], filename) # Usa a função auxiliar

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

    db.commit() # Commit das questões após o loop

    return RedirectResponse(url="/gestor/dashboard", status_code=303)

@router.get("/provas/editar/{prova_id}")
def editar_prova_page(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe a página para editar uma prova e suas questões."""
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
    gestor_id: int = Depends(verificar_gestor_sessao), # Protegido por gestor
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
    """Atualiza uma prova existente e suas questões."""
    # Atualizar a prova
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        return RedirectResponse(url="/provas/cadastrar", status_code=303)
    
    prova.materia = materia
    
    # Atualizar as questões
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    corretas = [
        corretas_1, corretas_2, corretas_3, corretas_4, corretas_5,
        corretas_6, corretas_7, corretas_8, corretas_9, corretas_10,
        corretas_11, corretas_12, corretas_13, corretas_14, corretas_15
    ]
    
    for i, questao in enumerate(questoes):
        if i < len(enunciados): # Garante que não tentamos acessar índices fora dos limites
            questao.enunciado = enunciados[i]
            questao.opcao_a = alternativas_A[i]
            questao.opcao_b = alternativas_B[i]
            questao.opcao_c = alternativas_C[i]
            questao.opcao_d = alternativas_D[i]
            questao.opcao_e = alternativas_E[i]
            questao.resposta_correta = corretas[i]
            
            # Atualizar imagem se fornecida
            if imagens and i < len(imagens) and imagens[i] and imagens[i].filename:
                # Opcional: Deletar foto antiga se existir
                if questao.imagem and os.path.exists(os.path.join("templates", questao.imagem.lstrip('/'))):
                    try:
                        os.remove(os.path.join("templates", questao.imagem.lstrip('/')))
                    except Exception as e:
                        print(f"Erro ao remover imagem antiga da questão {questao.id}: {e}")

                filename = f"questao_{prova_id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(imagens[i].filename).suffix}"
                questao.imagem = await salvar_imagem(imagens[i], filename) # Usa a função auxiliar
    
    db.commit()
    return RedirectResponse(url="/provas/cadastrar", status_code=303)

@router.post("/provas/excluir/{prova_id}")
def excluir_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exclui uma prova, suas questões, respostas e resultados associados."""
    try:
        # Buscar a prova para garantir que ela existe antes de tentar deletar
        prova = db.query(Prova).filter(Prova.id == prova_id).first()
        if not prova:
            return RedirectResponse(url="/provas/cadastrar", status_code=303)
        
        # 1. Deletar Respostas de Prova associadas às questões desta prova
        # Precisamos dos IDs das questões para filtrar corretamente
        questoes_ids = db.query(Questao.id).filter(Questao.prova_id == prova_id).all()
        # Converte a lista de tuplas (ex: [(1,), (2,)]) para uma lista simples de IDs (ex: [1, 2])
        questoes_ids = [q[0] for q in questoes_ids] 

        if questoes_ids: # Só tenta deletar se houver questões para a prova
            # Delete diretamente da tabela Resposta, filtrando pelos IDs das questões
            db.query(Resposta).filter(Resposta.questao_id.in_(questoes_ids)).delete(synchronize_session=False)
            print(f"Respostas para questões da prova {prova_id} removidas.")

        # 2. Deletar os Resultados associados à prova
        # Delete diretamente da tabela Resultado
        db.query(Resultado).filter(Resultado.prova_id == prova_id).delete(synchronize_session=False)
        print(f"Resultados da prova {prova_id} removidos.")

        # 3. Deletar as Questões da prova
        # Delete diretamente da tabela Questao
        db.query(Questao).filter(Questao.prova_id == prova_id).delete(synchronize_session=False)
        print(f"Questões da prova {prova_id} removidas.")

        # 4. Finalmente, deletar a própria Prova
        db.delete(prova) # Use o objeto 'prova' que já foi carregado
        db.commit() # Comita todas as deleções de uma vez
        print(f"Prova {prova_id} e seus dados relacionados excluídos com sucesso.")
            
    except SQLAlchemyError as e:
        db.rollback() # Desfaz todas as operações em caso de qualquer erro
        print(f"Erro ao excluir prova {prova_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao excluir a prova: {e}")
            
    return RedirectResponse(url="/provas/cadastrar", status_code=303)

# --- Rotas de Gerenciamento de Alunos ---
@router.get("/alunos")
def listar_alunos(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao), # Protegido por gestor
    curso: Optional[str] = Query(None),
    ano: Optional[str] = Query(None),
    situacao: Optional[str] = Query(None),
    nome: Optional[str] = Query(None),
    idade_min: Optional[int] = Query(None),
    idade_max: Optional[int] = Query(None),
    municipio: Optional[str] = Query(None),
    zona: Optional[str] = Query(None),
    origem_escolar: Optional[str] = Query(None),
):
    """Lista alunos, com filtros opcionais, e exibe notas por matéria."""
    # A lógica de consulta foi mantida aqui pois é específica da listagem de alunos,
    # não diretamente parte dos dashboards analíticos que moveremos.

    portugues = aliased(Prova)
    matematica = aliased(Prova)
    ciencias = aliased(Prova)

    # Subquery para calcular a média das notas
    media_subquery = (
        func.coalesce(
            db.query(Resultado.nota)
            .join(portugues, Resultado.prova_id == portugues.id)
            .filter(portugues.materia == "Português", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ) +
        func.coalesce(
            db.query(Resultado.nota)
            .join(matematica, Resultado.prova_id == matematica.id)
            .filter(matematica.materia == "Matemática", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ) +
        func.coalesce(
            db.query(Resultado.nota)
            .join(ciencias, Resultado.prova_id == ciencias.id)
            .filter(ciencias.materia == "Ciências", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        )
    ) / 3.0

    query = db.query(
        Aluno,
        func.coalesce(
            db.query(Resultado.nota)
            .join(portugues, Resultado.prova_id == portugues.id)
            .filter(portugues.materia == "Português", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_portugues"),
        func.coalesce(
            db.query(Resultado.nota)
            .join(matematica, Resultado.prova_id == matematica.id)
            .filter(matematica.materia == "Matemática", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_matematica"),
        func.coalesce(
            db.query(Resultado.nota)
            .join(ciencias, Resultado.prova_id == ciencias.id)
            .filter(ciencias.materia == "Ciências", Resultado.aluno_id == Aluno.idAluno)
            .scalar_subquery(),
            0,
        ).label("nota_ciencias"),
        media_subquery.label("media_geral")
    ).select_from(Aluno)

    # Aplicar filtros
    if curso:
        query = query.filter(Aluno.curso == curso)
    if ano:
        query = query.filter(Aluno.ano == ano)
    if nome:
        query = query.filter(Aluno.nome.ilike(f"%{nome}%"))
    if idade_min is not None:
        query = query.filter(Aluno.idade >= idade_min)
    if idade_max is not None:
        query = query.filter(Aluno.idade <= idade_max)
    if municipio:
        query = query.filter(Aluno.municipio.ilike(f"%{municipio}%"))
    if zona:
        query = query.filter(Aluno.zona == zona)
    if origem_escolar:
        query = query.filter(Aluno.origem_escolar == origem_escolar)

    # Filtro por situação baseado na média calculada (nota de 0-10)
    if situacao:
        if situacao == "suficiente":
            query = query.filter(media_subquery > 6.66)
        elif situacao == "regular":
            query = query.filter(media_subquery.between(3.34, 6.66))
        elif situacao == "insuficiente":
            query = query.filter(media_subquery <= 3.33)

    alunos = query.all()

    # Preparar filtros aplicados para o template
    filtros_aplicados = {}
    if curso: filtros_aplicados['curso'] = curso
    if ano: filtros_aplicados['ano'] = ano
    if situacao: filtros_aplicados['situacao'] = situacao
    if nome: filtros_aplicados['nome'] = nome
    if idade_min is not None: filtros_aplicados['idade_min'] = idade_min
    if idade_max is not None: filtros_aplicados['idade_max'] = idade_max
    if municipio: filtros_aplicados['municipio'] = municipio
    if zona: filtros_aplicados['zona'] = zona
    if origem_escolar: filtros_aplicados['origem_escolar'] = origem_escolar

    # Buscar municípios disponíveis para o filtro
    municipios_disponiveis = db.query(Aluno.municipio).distinct().order_by(Aluno.municipio).all()
    municipios_lista = [m[0] for m in municipios_disponiveis if m[0]]

    return templates.TemplateResponse(
        "gestor/gestor_alunos.html",
        {
            "request": request,
            "alunos": alunos,
            "filtros_aplicados": filtros_aplicados,
            "municipios_disponiveis": municipios_lista
        },
    )

@router.get("/alunos/cadastrar")
def cadastro_aluno_gestor_page(
    request: Request,
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe a página para o gestor cadastrar novos alunos."""
    return templates.TemplateResponse("gestor/gestor_cadastro.html", {"request": request})

@router.post("/alunos/upload/{aluno_id}")
def upload_imagem_aluno_gestor( # Renomeada para evitar conflito e clareza
    aluno_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Permite ao gestor fazer upload de imagem de perfil para um aluno existente."""
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first() # Corrigido para idAluno
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Salvar a imagem
    filename = f"aluno_{aluno_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(file.filename).suffix}"
    file_location = os.path.join(UPLOAD_DIR, "alunos", filename)
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Atualizar o caminho da imagem no banco (apenas o path relativo)
    aluno.imagem = f"/static/uploads/alunos/{filename}" # Caminho relativo com barra inicial
    db.commit()

    return {"message": "Imagem enviada com sucesso!", "path": aluno.imagem}

@router.get("/gestor/aluno/{aluno_id}/detalhes")
def detalhes_aluno_gestor(
    request: Request,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe os detalhes completos de um aluno específico para o gestor."""
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # Notas agregadas antigas (mantém retrocompatibilidade se ainda for útil no topo)
    portugues = aliased(Prova)
    matematica = aliased(Prova)
    ciencias = aliased(Prova)

    nota_portugues = db.query(Resultado.nota).join(portugues, Resultado.prova_id == portugues.id)\
        .filter(portugues.materia == "Português", Resultado.aluno_id == aluno_id).scalar()
    nota_matematica = db.query(Resultado.nota).join(matematica, Resultado.prova_id == matematica.id)\
        .filter(matematica.materia == "Matemática", Resultado.aluno_id == aluno_id).scalar()
    nota_ciencias = db.query(Resultado.nota).join(ciencias, Resultado.prova_id == ciencias.id)\
        .filter(ciencias.materia == "Ciências", Resultado.aluno_id == aluno_id).scalar()

    # Turmas do aluno (ativas)
    turmas_aluno = AlunoTurmaDAO.get_turmas_with_details_by_aluno(db, aluno_id)

    # Montar estrutura de provas por turma com resultado do aluno
    turmas_provas_resultados = []
    for at in turmas_aluno:
        turma = at.turma
        provas_turma = ProvaTurmaDAO.get_by_turma(db, turma.id)
        provas_com_resultado = []
        for pt in provas_turma:
            resultado = db.query(Resultado).filter(
                Resultado.aluno_id == aluno_id,
                Resultado.prova_id == pt.prova_id
            ).first()
            provas_com_resultado.append({
                "prova_turma": pt,
                "resultado": resultado
            })
        turmas_provas_resultados.append({
            "turma": turma,
            "provas": provas_com_resultado
        })

    # Respostas socioeconômicas agregadas (todas as respostas do aluno)
    respostas_rows = db.query(
        RespostaFormulario,
        PerguntaFormulario.enunciado,
        PerguntaFormulario.tipo_pergunta,
        PerguntaFormulario.opcoes
    ).join(PerguntaFormulario, RespostaFormulario.pergunta_id == PerguntaFormulario.id)\
     .filter(RespostaFormulario.aluno_id == aluno_id).all()

    respostas_socioeconomicas = {}
    import json as _json
    for resposta_obj, enunciado, tipo_pergunta, opcoes_json in respostas_rows:
        valor = None
        if resposta_obj.resposta_opcoes:
            try:
                valor = _json.loads(resposta_obj.resposta_opcoes)
            except Exception:
                valor = resposta_obj.resposta_opcoes
        elif resposta_obj.resposta_texto is not None:
            valor = resposta_obj.resposta_texto
        # Evita sobrescrever respostas repetidas; se houver múltiplas, acumula em lista
        if enunciado in respostas_socioeconomicas:
            existente = respostas_socioeconomicas[enunciado]
            if isinstance(existente, list):
                if isinstance(valor, list):
                    existente.extend(valor)
                else:
                    existente.append(valor)
                respostas_socioeconomicas[enunciado] = existente
            else:
                respostas_socioeconomicas[enunciado] = [existente] + (valor if isinstance(valor, list) else [valor])
        else:
            respostas_socioeconomicas[enunciado] = valor

    return templates.TemplateResponse(
        "gestor/detalhes_aluno.html",
        {
            "request": request,
            "aluno": aluno,
            "nota_portugues": nota_portugues,
            "nota_matematica": nota_matematica,
            "nota_ciencias": nota_ciencias,
            "turmas_provas_resultados": turmas_provas_resultados,
            "respostas_socioeconomicas": respostas_socioeconomicas
        }
    )

@router.get("/alunos/{aluno_id}")
def detalhes_aluno(
    request: Request,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe os detalhes e notas de um aluno específico para o gestor (rota de compatibilidade)."""
    return RedirectResponse(url=f"/gestor/aluno/{aluno_id}/detalhes", status_code=302)

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
    escola: Optional[str] = Form(None),
    forma_ingresso: Optional[str] = Form(None),
    acesso_internet: Optional[str] = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
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
    aluno.escola = escola
    aluno.forma_ingresso = forma_ingresso
    
    # Conversão para booleano para acesso_internet
    if acesso_internet == "true":
        aluno.acesso_internet = True
    elif acesso_internet == "false":
        aluno.acesso_internet = False
    else:
        aluno.acesso_internet = None

    # Atualizar foto se fornecida
    if foto:
        # Criar diretório se não existir
        os.makedirs("static/uploads/fotos", exist_ok=True)
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"foto_{aluno_id}_{timestamp}.jpg"
        filepath = f"static/uploads/fotos/{filename}"
        
        # Salvar arquivo
        with open(filepath, "wb") as buffer:
            content = await foto.read()
            buffer.write(content)
        
        # Atualizar caminho da foto no banco
        aluno.foto = f"/static/uploads/fotos/{filename}"

    db.commit()
    return RedirectResponse(url=f"/alunos/{aluno_id}", status_code=303)

@router.post("/gestor/alunos/{aluno_id}/editar-observacoes")
async def editar_observacoes_aluno(
    aluno_id: int,
    observacoes: str = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    aluno.observacoes = observacoes
    db.commit()
    return RedirectResponse(url=f"/alunos/{aluno_id}", status_code=303)

@router.post("/gestor/alunos/{aluno_id}/remover")
def remover_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    try:
        # Deletar dados relacionados (ordem importa devido a FKs)
        # Respostas de formulário
        RespostaFormularioDAO.delete_respostas_from_formulario_by_aluno(db, aluno_id, formulario_id=None)

        # Respostas de prova
        db.query(Resposta).filter(Resposta.aluno_id == aluno_id).delete(synchronize_session=False)

        # Resultados de prova
        db.query(Resultado).filter(Resultado.aluno_id == aluno_id).delete(synchronize_session=False)

        # Notificações do aluno
        db.query(Notificacao).filter(Notificacao.aluno_id == aluno_id).delete(synchronize_session=False)

        # Deletar o usuário correspondente ao aluno
        db.query(Usuario).filter(Usuario.id == aluno_id).delete(synchronize_session=False)

        # Deletar a imagem do aluno se existir
        if aluno.imagem:
            caminho_imagem = aluno.imagem.lstrip('/')
            caminho_completo = os.path.join("static", caminho_imagem)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                    print(f"Imagem do aluno removida: {caminho_completo}")
                except Exception as e:
                    print(f"Erro ao remover imagem do aluno: {e}")

        # Deletar o aluno
        db.delete(aluno)
        db.commit()
        print(f"Aluno {aluno_id} e todos os dados relacionados removidos com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao remover aluno {aluno_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao remover aluno: {e}")

    return RedirectResponse(url="/alunos", status_code=303)

# --- Rotas de Cadastro de Gestor (Público ou Restrito ao primeiro cadastro) ---
@router.get("/gestor/cadastrar")
def cadastrar_gestor_page(request: Request):
    """Exibe a página para cadastrar um novo gestor."""
    # Esta rota não está protegida por 'verificar_gestor_sessao' por padrão.
    # Se você quiser que SÓ gestores existentes cadastrem novos, adicione:
    # , gestor_id: int = Depends(verificar_gestor_sessao)
    return templates.TemplateResponse("gestor/cadastrar_gestor.html", {"request": request})

@router.post("/gestor/cadastrar")
async def cadastrar_gestor(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
    # Esta rota não está protegida por 'verificar_gestor_sessao' por padrão.
    # Se você quiser que SÓ gestores existentes cadastrem novos, adicione:
    # , gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cria um novo usuário e gestor no sistema."""
    # Verifica se já existe usuário com o mesmo email
    if db.query(Usuario).filter(Usuario.email == email).first():
        return templates.TemplateResponse("gestor/cadastrar_gestor.html", {"request": request, "erro": "E-mail já cadastrado."})
        
    # Cria o usuário
    senha_hash = bcrypt.hash(senha)
    novo_usuario = Usuario(email=email, senha_hash=senha_hash, tipo='gestor')
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario) # Atualiza o objeto para ter o ID gerado

    # Lida com upload de imagem
    imagem_path = None
    if foto and foto.filename:
        gestor_upload_dir = os.path.join(UPLOAD_DIR, "gestores")
        os.makedirs(gestor_upload_dir, exist_ok=True)
        filename = f"gestor_{novo_usuario.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(foto.filename).suffix}"
        file_location = os.path.join(gestor_upload_dir, filename)
        
        with open(file_location, "wb") as buffer:
            buffer.write(await foto.read())
        imagem_path = f"/static/uploads/gestores/{filename}" # Caminho relativo com barra inicial

    # Cria o gestor
    novo_gestor = Gestor(id=novo_usuario.id, nome=nome, imagem=imagem_path)
    db.add(novo_gestor)
    db.commit()

    return RedirectResponse(url="/gestor/dashboard", status_code=303)

# --- Rota do Dashboard do Gestor (Refatorada) ---
@router.get("/gestor/dashboard", response_class=HTMLResponse)
async def dashboard_gestor(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """
    Exibe o dashboard do gestor com dados analíticos.
    A lógica de coleta de dados é delegada ao AnalyticsService.
    """
    try:
        # CHAMA O SERVIÇO PARA OBTER TODOS OS DADOS DO DASHBOARD
        # Passa o gestor_id para o serviço, que pode usá-lo para buscar o objeto Gestor
        dashboard_data_full = AnalyticsService.get_dashboard_data_for_gestor(db, gestor_id)

        # O serviço retorna um dicionário com todos os dados, incluindo o objeto 'gestor'
        # Desempacotamos para passar separadamente se o template espera assim.
        gestor_obj = dashboard_data_full.pop('gestor') # Remove o objeto gestor do dicionário de dados

        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {
                "request": request,
                "dados": dashboard_data_full, # 'dados' agora contém os cards e dados dos gráficos
                "gestor": gestor_obj # Passa o objeto gestor separadamente
            }
        )
    except SQLAlchemyError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        # Buscar o gestor para passar ao template mesmo em caso de erro
        gestor = db.query(Gestor).filter(Gestor.id == gestor_id).first()
        # Retorna uma página de erro ou redireciona com mensagem
        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {
                "request": request, 
                "gestor": gestor,
                "erro": "Erro ao carregar os dados do dashboard."
            },
            status_code=500
        )

# === ROTAS DE GERENCIAMENTO DE PROFESSORES ===

@router.get("/gestor/professores")
def listar_professores(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista todos os professores cadastrados"""
    professores = ProfessorDAO.get_all_with_campus(db)
    return templates.TemplateResponse(
        "gestor/gestor_professores.html",
        {"request": request, "professores": professores}
    )

@router.get("/gestor/professores/cadastrar")
def cadastrar_professor_page(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Página para gestor cadastrar professor"""
    campus = CampusDAO.get_all(db)
    return templates.TemplateResponse(
        "gestor/cadastrar_professor.html",
        {"request": request, "campus": campus}
    )

@router.post("/gestor/professores/cadastrar")
async def cadastrar_professor_gestor(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    campus_id: int = Form(...),
    especialidade: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Processa cadastro de professor pelo gestor"""
    # Verificar se campus existe
    campus = CampusDAO.get_by_id(db, campus_id)
    if not campus:
        campus_list = CampusDAO.get_all(db)
        return templates.TemplateResponse(
            "gestor/cadastrar_professor.html",
            {"request": request, "campus": campus_list, "erro": "Campus inválido"}
        )
    
    # Processar upload de foto
    imagem_path = None
    if foto and foto.filename:
        professor_upload_dir = os.path.join(UPLOAD_DIR, "professores")
        os.makedirs(professor_upload_dir, exist_ok=True)
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
            "gestor/cadastrar_professor.html",
            {"request": request, "campus": campus_list, "erro": "E-mail já cadastrado"}
        )
    
    return RedirectResponse(url="/gestor/professores", status_code=303)

@router.get("/gestor/turmas")
def listar_turmas_gestor(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista todas as turmas de todos os professores"""
    turmas = TurmaDAO.get_all_with_details(db)
    return templates.TemplateResponse(
        "gestor/gestor_turmas.html",
        {"request": request, "turmas": turmas}
    )

@router.get("/gestor/provas-professores")
def listar_provas_professores(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista todas as provas criadas pelos professores"""
    from sqlalchemy.orm import joinedload
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    provas = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.prova_questoes)
    ).filter(Prova.professor_id.isnot(None)).order_by(Prova.data_criacao.desc()).all()
    return templates.TemplateResponse(
        "gestor/gestor_provas_professores.html",
        {"request": request, "provas": provas}
    )

# === ROTAS DE DETALHES PARA GESTOR ===

@router.get("/gestor/turma/{turma_id}/detalhes")
def detalhes_turma_gestor(
    request: Request,
    turma_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Detalhes de uma turma específica com alunos e provas"""
    from sqlalchemy.orm import joinedload
    from models.aluno_turma import AlunoTurma
    from models.prova_turma import ProvaTurma
    
    # Buscar turma com todos os dados relacionados
    turma = db.query(Turma).options(
        joinedload(Turma.professor),
        joinedload(Turma.campus),
        joinedload(Turma.aluno_turmas).joinedload(AlunoTurma.aluno),
        joinedload(Turma.prova_turmas).joinedload(ProvaTurma.prova)
    ).filter(Turma.id == turma_id).first()
    
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    # Buscar estatísticas da turma
    total_alunos = len(turma.aluno_turmas)
    total_provas = len(turma.prova_turmas)
    
    return templates.TemplateResponse(
        "gestor/detalhes_turma.html",
        {
            "request": request, 
            "turma": turma,
            "total_alunos": total_alunos,
            "total_provas": total_provas
        }
    )

@router.get("/gestor/turma/{turma_id}/alunos")
def alunos_turma_gestor(
    request: Request,
    turma_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista alunos de uma turma específica"""
    from sqlalchemy.orm import joinedload
    from models.aluno_turma import AlunoTurma
    
    # Buscar turma com dados relacionados
    turma = db.query(Turma).options(
        joinedload(Turma.professor),
        joinedload(Turma.campus),
        joinedload(Turma.aluno_turmas).joinedload(AlunoTurma.aluno)
    ).filter(Turma.id == turma_id).first()
    
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    return templates.TemplateResponse(
        "gestor/alunos_turma.html",
        {"request": request, "turma": turma}
    )

@router.get("/gestor/turma/{turma_id}/provas")
def provas_turma_gestor(
    request: Request,
    turma_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista provas de uma turma específica"""
    from sqlalchemy.orm import joinedload
    from models.prova_turma import ProvaTurma
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    
    # Buscar turma com dados relacionados
    turma = db.query(Turma).options(
        joinedload(Turma.professor),
        joinedload(Turma.campus),
        joinedload(Turma.prova_turmas).joinedload(ProvaTurma.prova)
    ).filter(Turma.id == turma_id).first()
    
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    
    return templates.TemplateResponse(
        "gestor/provas_turma.html",
        {"request": request, "turma": turma}
    )

@router.post("/gestor/turma/{turma_id}/remover-aluno/{aluno_id}")
def remover_aluno_turma(
    turma_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Remove um aluno de uma turma"""
    from models.aluno_turma import AlunoTurma, StatusAlunoTurma
    
    # Buscar a relação aluno-turma
    aluno_turma = db.query(AlunoTurma).filter(
        AlunoTurma.turma_id == turma_id,
        AlunoTurma.aluno_id == aluno_id,
        AlunoTurma.status == StatusAlunoTurma.ATIVO
    ).first()
    
    if not aluno_turma:
        raise HTTPException(status_code=404, detail="Aluno não encontrado na turma")
    
    # Marcar como removido em vez de deletar
    aluno_turma.status = StatusAlunoTurma.REMOVIDO
    db.commit()
    
    return RedirectResponse(url=f"/gestor/turma/{turma_id}/detalhes", status_code=303)

@router.post("/gestor/turma/{turma_id}/adicionar-aluno/{aluno_id}")
def adicionar_aluno_turma(
    turma_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Adiciona um aluno de volta a uma turma"""
    from models.aluno_turma import AlunoTurma, StatusAlunoTurma
    
    # Buscar a relação aluno-turma
    aluno_turma = db.query(AlunoTurma).filter(
        AlunoTurma.turma_id == turma_id,
        AlunoTurma.aluno_id == aluno_id,
        AlunoTurma.status == StatusAlunoTurma.REMOVIDO
    ).first()
    
    if not aluno_turma:
        raise HTTPException(status_code=404, detail="Aluno não encontrado na turma")
    
    # Marcar como ativo novamente
    aluno_turma.status = StatusAlunoTurma.ATIVO
    db.commit()
    
    return RedirectResponse(url=f"/gestor/turma/{turma_id}/alunos", status_code=303)

@router.get("/gestor/prova/{prova_id}/detalhes")
def detalhes_prova_gestor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Detalhes de uma prova específica com turmas e resultados"""
    from sqlalchemy.orm import joinedload
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    prova = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.prova_questoes).joinedload(ProvaQuestao.questao_banco),
        joinedload(Prova.prova_turmas).joinedload(ProvaTurma.turma),
        joinedload(Prova.resultados).joinedload(Resultado.aluno)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    # Buscar resultados da prova
    resultados = db.query(Resultado).options(
        joinedload(Resultado.aluno)
    ).filter(Resultado.prova_id == prova_id).all()
    
    return templates.TemplateResponse(
        "gestor/detalhes_prova.html",
        {"request": request, "prova": prova, "resultados": resultados}
    )

@router.get("/gestor/prova/{prova_id}/turmas")
def turmas_prova_gestor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Lista turmas de uma prova específica"""
    from sqlalchemy.orm import joinedload
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    prova = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.prova_turmas).joinedload(ProvaTurma.turma)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    return templates.TemplateResponse(
        "gestor/turmas_prova.html",
        {"request": request, "prova": prova}
    )

@router.get("/gestor/prova/{prova_id}/resultados")
def resultados_prova_gestor(
    request: Request,
    prova_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Resultados de uma prova específica"""
    from sqlalchemy.orm import joinedload
    
    # Verificar e atualizar provas expiradas antes de qualquer visualização
    from dao.prova_turma_dao import ProvaTurmaDAO
    ProvaTurmaDAO.check_and_update_expired(db)
    prova = db.query(Prova).options(
        joinedload(Prova.professor),
        joinedload(Prova.resultados).joinedload(Resultado.aluno)
    ).filter(Prova.id == prova_id).first()
    
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    
    return templates.TemplateResponse(
        "gestor/resultados_prova.html",
        {"request": request, "prova": prova}
    )

@router.get("/relatorios")
async def relatorios_gestor(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Página de relatórios do gestor com gráficos Chart.js"""
    dados = RelatorioService.get_gestor_report_data(db)
    return templates.TemplateResponse(
        "gestor/relatorios.html",
        {"request": request, "dados": dados}
    )

@router.get("/gestor/relatorios/export/pdf")
async def export_relatorios_gestor_pdf(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    dados = RelatorioService.get_gestor_report_data(db)
    template = templates.get_template("gestor/relatorios.html")
    html = template.render(request=request, dados=dados)
    return pdf_response_from_html(html, filename="relatorio_gestor.pdf")

@router.get("/gestor/relatorios/export/docx")
async def export_relatorios_gestor_docx(
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    dados = RelatorioService.get_gestor_report_data(db)
    sections = {
        "Médias por Matéria": dados["materias"],
        "Médias por Curso": dados["cursos"],
        "Participação": dados["participacao"],
    }
    return docx_response_from_data("Relatório do Gestor", sections, filename="relatorio_gestor.docx")

# ===== ROTAS DE GERENCIAMENTO DE USUÁRIOS =====

@router.get("/gestor/gerenciar-usuarios")
def gerenciar_usuarios(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Página de gerenciamento de usuários"""
    from sqlalchemy.orm import joinedload
    from models.aluno import Aluno
    from models.professor import Professor
    from models.gestor import Gestor
    from models.campus import Campus
    
    # Buscar todos os usuários
    alunos = db.query(Aluno).options(joinedload(Aluno.usuario)).all()
    professores = db.query(Professor).options(
        joinedload(Professor.usuario),
        joinedload(Professor.campus)
    ).all()
    gestores = db.query(Gestor).options(joinedload(Gestor.usuario)).all()
    campus_list = db.query(Campus).options(
        joinedload(Campus.professores),
        joinedload(Campus.turmas)
    ).all()
    
    # Contar totais
    total_alunos = len(alunos)
    total_professores = len(professores)
    total_gestores = len(gestores)
    total_campus = len(campus_list)
    total_usuarios = total_alunos + total_professores + total_gestores
    
    return templates.TemplateResponse(
        "gestor/gerenciar_usuarios.html",
        {
            "request": request,
            "alunos": alunos,
            "professores": professores,
            "gestores": gestores,
            "campus_list": campus_list,
            "total_alunos": total_alunos,
            "total_professores": total_professores,
            "total_gestores": total_gestores,
            "total_campus": total_campus,
            "total_usuarios": total_usuarios
        }
    )

@router.post("/gestor/cadastrar-aluno")
async def cadastrar_aluno(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    curso: str = Form(...),
    ano: int = Form(...),
    imagem: UploadFile = File(None),
    imagem_cortada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cadastra um novo aluno"""
    from models.aluno import Aluno
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    from datetime import datetime
    
    # Verificar se email já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    try:
        # Criar usuário
        usuario = Usuario(
            email=email,
            senha_hash=criptografar_senha(senha),
            tipo="aluno"
        )
        db.add(usuario)
        db.flush()  # Para obter o ID
        
        # Processar imagem se fornecida
        imagem_path = None
        upload_dir = "templates/static/uploads/alunos"
        os.makedirs(upload_dir, exist_ok=True)
        if imagem_cortada:
            try:
                import base64
                header, b64data = imagem_cortada.split(",", 1) if "," in imagem_cortada else ("", imagem_cortada)
                img_bytes = base64.b64decode(b64data)
                filename = f"{usuario.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                imagem_path = "/static/uploads/alunos/" + filename
            except Exception as e:
                print(f"Falha ao salvar imagem cortada (aluno): {e}")
        elif imagem and imagem.filename:
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            imagem_path = "/static/uploads/alunos/" + filename
        
        # Criar aluno
        aluno = Aluno(
            idUser=usuario.id,
            nome=nome,
            curso=curso,
            ano=ano,
            imagem=imagem_path,
            idade=18,  # Valor padrão
            municipio="Não informado",  # Valor padrão
            zona="urbana",  # Valor padrão
            origem_escolar="pública"  # Valor padrão
        )
        db.add(aluno)
        db.commit()
        
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar aluno: {str(e)}")

@router.post("/gestor/cadastrar-professor")
async def cadastrar_professor(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    campus_id: int = Form(...),
    imagem: UploadFile = File(None),
    imagem_cortada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cadastra um novo professor"""
    from models.professor import Professor
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    from datetime import datetime
    
    # Verificar se email já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    try:
        # Criar usuário
        usuario = Usuario(
            email=email,
            senha_hash=criptografar_senha(senha),
            tipo="professor"
        )
        db.add(usuario)
        db.flush()  # Para obter o ID
        
        # Processar imagem se fornecida
        imagem_path = None
        upload_dir = "templates/static/uploads/professores"
        os.makedirs(upload_dir, exist_ok=True)
        if imagem_cortada:
            try:
                import base64
                header, b64data = imagem_cortada.split(",", 1) if "," in imagem_cortada else ("", imagem_cortada)
                img_bytes = base64.b64decode(b64data)
                filename = f"{usuario.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                imagem_path = "/static/uploads/professores/" + filename
            except Exception as e:
                print(f"Falha ao salvar imagem cortada (professor): {e}")
        elif imagem and imagem.filename:
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            imagem_path = "/static/uploads/professores/" + filename
        
        # Criar professor
        professor = Professor(
            id=usuario.id,
            nome=nome,
            imagem=imagem_path,
            campus_id=campus_id
        )
        db.add(professor)
        db.commit()
        
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar professor: {str(e)}")

@router.post("/gestor/cadastrar-gestor")
async def cadastrar_gestor(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    imagem: UploadFile = File(None),
    imagem_cortada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cadastra um novo gestor"""
    from models.gestor import Gestor
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    from datetime import datetime
    
    # Verificar se email já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    try:
        # Criar usuário
        usuario = Usuario(
            email=email,
            senha_hash=criptografar_senha(senha),
            tipo="gestor"
        )
        db.add(usuario)
        db.flush()  # Para obter o ID
        
        # Processar imagem se fornecida
        imagem_path = None
        upload_dir = "templates/static/uploads/gestores"
        os.makedirs(upload_dir, exist_ok=True)
        if imagem_cortada:
            try:
                import base64
                header, b64data = imagem_cortada.split(",", 1) if "," in imagem_cortada else ("", imagem_cortada)
                img_bytes = base64.b64decode(b64data)
                filename = f"{usuario.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                imagem_path = "/static/uploads/gestores/" + filename
            except Exception as e:
                print(f"Falha ao salvar imagem cortada (gestor): {e}")
        elif imagem and imagem.filename:
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            imagem_path = "/static/uploads/gestores/" + filename
        
        # Criar gestor
        gestor = Gestor(
            id=usuario.id,
            nome=nome,
            imagem=imagem_path
        )
        db.add(gestor)
        db.commit()
        
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar gestor: {str(e)}")

@router.post("/gestor/editar-aluno/{aluno_id}")
async def editar_aluno(
    aluno_id: int,
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    curso: str = Form(...),
    ano: int = Form(...),
    senha: str = Form(None),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Edita um aluno existente"""
    from models.aluno import Aluno
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    
    try:
        # Buscar o aluno
        aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Buscar o usuário associado
        usuario = db.query(Usuario).filter(Usuario.id == aluno.idUser).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verificar se email já existe em outro usuário
        if email != usuario.email:
            usuario_existente = db.query(Usuario).filter(
                Usuario.email == email,
                Usuario.id != usuario.id
            ).first()
            if usuario_existente:
                raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Atualizar dados do usuário
        if senha and senha.strip():
            # Atualizar email e senha
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email,
                "senha_hash": criptografar_senha(senha)
            })
        else:
            # Atualizar apenas email
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email
            })
        
        # Atualizar dados do aluno
        aluno.nome = nome
        aluno.curso = curso
        aluno.ano = ano
        
        # Processar nova imagem se fornecida
        if imagem and imagem.filename:
            upload_dir = "templates/static/uploads/alunos"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            aluno.imagem = "/static/uploads/alunos/" + filename
        
        db.commit()
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar aluno: {str(e)}")

@router.post("/gestor/cadastrar-campus")
def cadastrar_campus(
    nome: str = Form(...),
    endereco: str = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Cadastra um novo campus"""
    from dao.campus_dao import CampusDAO
    
    try:
        CampusDAO.create(db, nome=nome, endereco=endereco)
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar campus: {str(e)}")

@router.post("/gestor/editar-campus/{campus_id}")
def editar_campus(
    campus_id: int,
    nome: str = Form(...),
    endereco: str = Form(None),
    ativo: str = Form(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Edita um campus existente"""
    from dao.campus_dao import CampusDAO
    
    try:
        ativo_bool = ativo == "true" if ativo else None
        CampusDAO.update(db, campus_id, nome=nome, endereco=endereco, ativo=ativo_bool)
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar campus: {str(e)}")

@router.post("/gestor/excluir-campus/{campus_id}")
def excluir_campus(
    campus_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Exclui permanentemente um campus"""
    from dao.campus_dao import CampusDAO
    
    try:
        # Verificar se o campus tem professores ou turmas associadas
        campus = CampusDAO.get_by_id(db, campus_id)
        if not campus:
            raise HTTPException(status_code=404, detail="Campus não encontrado")
        
        if campus.professores or campus.turmas:
            raise HTTPException(status_code=400, detail="Não é possível excluir campus com professores ou turmas associadas")
        
        CampusDAO.hard_delete(db, campus_id)
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir campus: {str(e)}")

@router.post("/gestor/editar-professor/{professor_id}")
async def editar_professor(
    professor_id: int,
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    campus_id: int = Form(...),
    senha: str = Form(None),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Edita um professor existente"""
    from models.professor import Professor
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    
    try:
        # Buscar o professor
        professor = db.query(Professor).filter(Professor.id == professor_id).first()
        if not professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        
        # Buscar o usuário associado
        usuario = db.query(Usuario).filter(Usuario.id == professor.id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verificar se email já existe em outro usuário
        if email != usuario.email:
            usuario_existente = db.query(Usuario).filter(
                Usuario.email == email,
                Usuario.id != usuario.id
            ).first()
            if usuario_existente:
                raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Atualizar dados do usuário
        if senha and senha.strip():
            # Atualizar email e senha
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email,
                "senha_hash": criptografar_senha(senha)
            })
        else:
            # Atualizar apenas email
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email
            })
        
        # Atualizar dados do professor
        professor.nome = nome
        professor.campus_id = campus_id
        
        # Processar nova imagem se fornecida
        if imagem and imagem.filename:
            upload_dir = "templates/static/uploads/professores"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            professor.imagem = "/static/uploads/professores/" + filename
        
        db.commit()
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar professor: {str(e)}")

@router.post("/gestor/editar-gestor/{gestor_id}")
async def editar_gestor(
    gestor_id: int,
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(None),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    gestor_logado_id: int = Depends(verificar_gestor_sessao)
):
    """Edita um gestor existente"""
    from models.gestor import Gestor
    from models.usuario import Usuario
    from dao.senhaHash import criptografar_senha
    import os
    
    try:
        # Buscar o gestor
        gestor = db.query(Gestor).filter(Gestor.id == gestor_id).first()
        if not gestor:
            raise HTTPException(status_code=404, detail="Gestor não encontrado")
        
        # Buscar o usuário associado
        usuario = db.query(Usuario).filter(Usuario.id == gestor.id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verificar se email já existe em outro usuário
        if email != usuario.email:
            usuario_existente = db.query(Usuario).filter(
                Usuario.email == email,
                Usuario.id != usuario.id
            ).first()
            if usuario_existente:
                raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Atualizar dados do usuário
        if senha and senha.strip():
            # Atualizar email e senha
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email,
                "senha_hash": criptografar_senha(senha)
            })
        else:
            # Atualizar apenas email
            db.query(Usuario).filter(Usuario.id == usuario.id).update({
                "email": email
            })
        
        # Atualizar dados do gestor
        gestor.nome = nome
        
        # Processar nova imagem se fornecida
        if imagem and imagem.filename:
            upload_dir = "templates/static/uploads/gestores"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{usuario.id}_{imagem.filename}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                content = await imagem.read()
                buffer.write(content)
            gestor.imagem = "/static/uploads/gestores/" + filename
        
        db.commit()
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao editar gestor: {str(e)}")

@router.post("/gestor/excluir-aluno/{aluno_id}")
def excluir_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Exclui um aluno permanentemente"""
    from models.aluno import Aluno
    from models.usuario import Usuario
    from models.aluno_turma import AlunoTurma
    from dao.aluno_turma_dao import AlunoTurmaDAO
    
    try:
        # Buscar o aluno
        aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Remover aluno de todas as turmas primeiro
        turmas_aluno = AlunoTurmaDAO.get_turmas_by_aluno(db, aluno_id)
        for aluno_turma in turmas_aluno:
            AlunoTurmaDAO.hard_remove_aluno_from_turma(db, aluno_id, aluno_turma.turma_id)
        
        # Deletar dados relacionados (ordem importa devido a FKs)
        # Respostas de formulário
        RespostaFormularioDAO.delete_respostas_from_formulario_by_aluno(db, aluno_id, formulario_id=None)

        # Respostas de prova
        db.query(Resposta).filter(Resposta.aluno_id == aluno_id).delete(synchronize_session=False)

        # Resultados de prova
        db.query(Resultado).filter(Resultado.aluno_id == aluno_id).delete(synchronize_session=False)

        # Notificações do aluno
        db.query(Notificacao).filter(Notificacao.aluno_id == aluno_id).delete(synchronize_session=False)

        # Deletar a imagem do aluno se existir
        if aluno.imagem:
            caminho_imagem = aluno.imagem.lstrip('/')
            caminho_completo = os.path.join("static", caminho_imagem)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                    print(f"Imagem do aluno removida: {caminho_completo}")
                except Exception as e:
                    print(f"Erro ao remover imagem do aluno: {e}")

        # Deletar o usuário (cascade vai excluir o aluno)
        usuario = db.query(Usuario).filter(Usuario.id == aluno.idUser).first()
        if usuario:
            db.delete(usuario)
        
        db.commit()
        print(f"Aluno {aluno_id} e todos os dados relacionados removidos com sucesso.")
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao remover aluno {aluno_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir aluno: {str(e)}")

@router.post("/gestor/excluir-professor/{professor_id}")
def excluir_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """Exclui um professor permanentemente"""
    from models.professor import Professor
    from models.usuario import Usuario
    
    try:
        # Buscar o professor
        professor = db.query(Professor).filter(Professor.id == professor_id).first()
        if not professor:
            raise HTTPException(status_code=404, detail="Professor não encontrado")
        
        # Verificar se o professor tem turmas associadas
        if professor.turmas:
            raise HTTPException(status_code=400, detail="Não é possível excluir professor com turmas associadas")
        
        # Excluir o usuário (cascade vai excluir o professor)
        usuario = db.query(Usuario).filter(Usuario.id == professor.id).first()
        if usuario:
            db.delete(usuario)
        
        db.commit()
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir professor: {str(e)}")

@router.post("/gestor/excluir-gestor/{gestor_id}")
def excluir_gestor(
    gestor_id: int,
    db: Session = Depends(get_db),
    gestor_logado_id: int = Depends(verificar_gestor_sessao)
):
    """Exclui um gestor permanentemente"""
    from models.gestor import Gestor
    from models.usuario import Usuario
    
    try:
        # Verificar se não está tentando excluir a si mesmo
        if gestor_id == gestor_logado_id:
            raise HTTPException(status_code=400, detail="Não é possível excluir a si mesmo")
        
        # Buscar o gestor
        gestor = db.query(Gestor).filter(Gestor.id == gestor_id).first()
        if not gestor:
            raise HTTPException(status_code=404, detail="Gestor não encontrado")
        
        # Excluir o usuário (cascade vai excluir o gestor)
        usuario = db.query(Usuario).filter(Usuario.id == gestor.id).first()
        if usuario:
            db.delete(usuario)
        
        db.commit()
        return RedirectResponse(url="/gestor/gerenciar-usuarios", status_code=303)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir gestor: {str(e)}")

# === ROTA PARA GERAR RELATÓRIO DO DASHBOARD ===

@router.get("/gestor/dashboard/relatorio")
async def gerar_relatorio_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao)
):
    """
    Gera e baixa um relatório DOCX completo com todas as informações do dashboard.
    """
    try:
        # Gerar o relatório usando o serviço
        relatorio_buffer = RelatorioService.gerar_relatorio_geral_dashboard(db, gestor_id)
        
        # Criar nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_geral_dashboard_{timestamp}.docx"
        
        # Retornar o arquivo para download
        from fastapi.responses import Response
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        return Response(
            content=relatorio_buffer.read(),
            headers=headers,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar relatório: {str(e)}"
        )