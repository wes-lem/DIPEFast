import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, distinct, and_

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

from controllers.usuario_controller import verificar_sessao

from services.graficos_service import AnalyticsService

from dao.aluno_dao import AlunoDAO
from dao.resposta_formulario_dao import RespostaFormularioDAO
from dao.notificacao_dao import NotificacaoDAO

from utils.auth import verificar_gestor_sessao

# Importar a instância templates do app_config
from app_config import templates

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
):
    """Lista alunos, com filtros opcionais, e exibe notas por matéria."""
    # A lógica de consulta foi mantida aqui pois é específica da listagem de alunos,
    # não diretamente parte dos dashboards analíticos que moveremos.
    
    portugues = aliased(Prova)
    matematica = aliased(Prova)
    ciencias = aliased(Prova)

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

    if curso:
        query = query.filter(Aluno.curso == curso)
    if ano:
        query = query.filter(Aluno.ano == ano)
    if situacao:
        query = query.filter(Aluno.situacao == situacao) # Se você tiver 'situacao' no modelo Aluno, ou precisa calcular/join com Resultado

    alunos = query.all()

    return templates.TemplateResponse(
        "gestor/gestor_alunos.html",
        {
            "request": request,
            "alunos": alunos
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

@router.get("/alunos/{aluno_id}")
def detalhes_aluno(
    request: Request,
    aluno_id: int,
    db: Session = Depends(get_db),
    gestor_id: int = Depends(verificar_gestor_sessao) # Protegido por gestor
):
    """Exibe os detalhes e notas de um aluno específico para o gestor."""
    aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
    if not aluno:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # Buscar notas das provas (mantido, pois é específico para detalhes de um aluno)
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
        # Retorna uma página de erro ou redireciona com mensagem
        return templates.TemplateResponse(
            "gestor/dashboard_gestor.html",
            {"request": request, "erro": "Erro ao carregar os dados do dashboard."},
            status_code=500
        )