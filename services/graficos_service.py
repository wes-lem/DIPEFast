from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_
from models.aluno import Aluno
from models.prova import Prova
from models.professor import Professor
from models.gestor import Gestor
from models.resultado import Resultado
from models.gestor import Gestor # Para buscar dados do gestor, se necessário
import unicodedata

def normalizar_materia(materia: str) -> str:
    """
    Normaliza o nome da matéria removendo acentos, convertendo para minúsculas
    e tratando variações de 'Ciências'
    """
    if not materia:
        return ""
    
    # Remove acentos
    materia_sem_acento = unicodedata.normalize('NFD', materia)
    materia_sem_acento = ''.join(char for char in materia_sem_acento if unicodedata.category(char) != 'Mn')
    
    # Converte para minúsculas
    materia_lower = materia_sem_acento.lower().strip()
    
    # Trata variações de Ciências (incluindo "Ciências da Natureza")
    if 'ciencias' in materia_lower or 'ciencia' in materia_lower:
        return 'ciencias'
    
    # Trata variações de Português
    if 'portugues' in materia_lower:
        return 'portugues'
    
    # Trata variações de Matemática
    if 'matematica' in materia_lower:
        return 'matematica'
    
    return materia_lower

def obter_materia_padrao(materia_normalizada: str) -> str:
    """
    Retorna o nome padrão da matéria baseado na versão normalizada
    """
    if materia_normalizada == 'ciencias':
        return 'Ciências'
    elif materia_normalizada == 'portugues':
        return 'Português'
    elif materia_normalizada == 'matematica':
        return 'Matemática'
    return materia_normalizada.title()

class AnalyticsService:
    @staticmethod
    def get_dashboard_data_for_gestor(db: Session, gestor_id: int):
        """
        Coleta e processa todos os dados analíticos para o dashboard do gestor.
        """
        # Buscar informações do gestor logado
        gestor = db.query(Gestor).filter(Gestor.id == gestor_id).first()
        # Se não houver gestor, você pode decidir como lidar (ex: retornar None, ou raise HTTPException)
        # Para este serviço, assumimos que o gestor_id é válido, pois já foi verificado pelo controller.

        # Dados para os cards
        total_alunos = db.query(func.count(Aluno.idAluno)).scalar() or 0
        total_professores = db.query(func.count(Professor.id)).scalar() or 0
        total_provas = db.query(func.count(distinct(Resultado.prova_id))).scalar() or 0
        total_gestores = db.query(func.count(distinct(Gestor.id))).scalar() or 0
        total_usuarios = total_alunos + total_professores + total_gestores
        
        # Calcular média geral
        resultados_acertos = db.query(Resultado.acertos).all()
        media_geral = 0
        total_suficiente = 0
        if resultados_acertos:
            media_geral = sum(r.acertos for r in resultados_acertos) / len(resultados_acertos)
            total_suficiente = sum(1 for r in resultados_acertos if r.acertos >= 7)
            percentual_suficiente = (total_suficiente / len(resultados_acertos)) * 100
        else:
            percentual_suficiente = 0
            
        cards = {
            'total_alunos': total_alunos,
            'total_professores': total_professores,
            'total_gestores': total_gestores,
            'total_usuarios': total_usuarios,
            'total_provas': total_provas,
            'media_geral': f"{media_geral:.1f}",
            'percentual_suficiente': f"{percentual_suficiente:.1f}"
        }

        # Dados para os gráficos (cores hardcoded aqui, mas poderiam vir de config ou ser passadas)
        # Atenção: as cores aqui são literais RGBA, não as variáveis CSS.
        # No template, o JS usará essas cores.
        cores_geral = {
            'portugues': 'rgba(255, 99, 132, 0.8)',
            'matematica': 'rgba(54, 162, 235, 0.8)',
            'ciencias': 'rgba(255, 206, 86, 0.8)',
            'urbana': 'rgba(75, 192, 192, 0.8)',
            'rural': 'rgba(153, 102, 255, 0.8)',
            'insuficiente': 'rgba(255, 99, 132, 0.8)',
            'regular': 'rgba(255, 206, 86, 0.8)',
            'suficiente': 'rgba(75, 192, 192, 0.8)',
            'participaram': 'rgba(75, 192, 192, 0.8)',
            'nao_participaram': 'rgba(255, 99, 132, 0.8)'
        }


        # Distribuição por zona
        zona_distribuicao = {
            'labels': ['Urbana', 'Rural'],
            'data': [
                db.query(Aluno).filter(Aluno.zona == 'urbana').count(),
                db.query(Aluno).filter(Aluno.zona == 'rural').count()
            ],
            'cores': [cores_geral['urbana'], cores_geral['rural']]
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

        # Desempenho por disciplina (agrupando variações de capitalização e acentuação)
        # Buscar todas as matérias distintas das provas
        materias_distintas = db.query(Prova.materia).distinct().all()
        materias_dict = {}  # {materia_normalizada: [materias_originais]}
        
        for (materia_original,) in materias_distintas:
            materia_norm = normalizar_materia(materia_original)
            if materia_norm not in materias_dict:
                materias_dict[materia_norm] = []
            materias_dict[materia_norm].append(materia_original)
        
        # Calcular média de acertos para cada matéria normalizada
        desempenho_data = []
        desempenho_labels = []
        
        # Ordem padrão: Português, Matemática, Ciências
        ordem_materias = ['portugues', 'matematica', 'ciencias']
        
        for materia_norm in ordem_materias:
            if materia_norm in materias_dict:
                # Buscar todas as variações desta matéria
                materias_variacoes = materias_dict[materia_norm]
                # Calcular média considerando todas as variações
                media = db.query(func.avg(Resultado.acertos)).join(
                    Prova, Resultado.prova_id == Prova.id
                ).filter(
                    Prova.materia.in_(materias_variacoes)
                ).scalar() or 0
                
                desempenho_labels.append(obter_materia_padrao(materia_norm))
                desempenho_data.append(float(media))
        
        # Adicionar outras matérias que não sejam as três padrão (se houver)
        for materia_norm, materias_originais in materias_dict.items():
            if materia_norm not in ordem_materias:
                media = db.query(func.avg(Resultado.acertos)).join(
                    Prova, Resultado.prova_id == Prova.id
                ).filter(
                    Prova.materia.in_(materias_originais)
                ).scalar() or 0
                
                # Usar a primeira matéria original como label (ou normalizar)
                desempenho_labels.append(materias_originais[0])
                desempenho_data.append(float(media))
        
        desempenho_disciplina = {
            'labels': desempenho_labels,
            'data': desempenho_data
        }

        # Distribuição das notas (usando a coluna situacao que já está salva no banco)
        distribuicao_notas = {
            'labels': ['Insuficiente', 'Regular', 'Suficiente'],
            'data': [
                db.query(func.count(Resultado.id)).filter(Resultado.situacao == 'Insuficiente').scalar() or 0,
                db.query(func.count(Resultado.id)).filter(Resultado.situacao == 'Regular').scalar() or 0,
                db.query(func.count(Resultado.id)).filter(Resultado.situacao == 'Suficiente').scalar() or 0
            ]
        }

        # Progressão dos Alunos (média geral por ano)
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

        # Comparação entre Turmas (média geral por curso)
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

        # Taxa de Participação
        total_alunos_in_db = db.query(func.count(Aluno.idAluno)).scalar() or 0
        alunos_com_resultado = db.query(Resultado.aluno_id).distinct().count()
        taxa_participacao = {
            'labels': ['Participaram', 'Não participaram'],
            'data': [alunos_com_resultado, max(0, total_alunos_in_db - alunos_com_resultado)]
        }

        # Top 10 Alunos (maior média)
        alunos_all = db.query(Aluno).all() # Renomeado para evitar conflito com 'alunos' aliased
        top_alunos_lista = []
        for aluno in alunos_all:
            resultados_aluno = db.query(Resultado).filter(Resultado.aluno_id == aluno.idAluno).all()
            notas = [r.acertos for r in resultados_aluno]
            media = sum(notas) / len(notas) if notas else 0
            
            # Buscar provas do aluno com suas matérias
            provas_aluno = {}
            for resultado in resultados_aluno:
                prova = db.query(Prova).filter(Prova.id == resultado.prova_id).first()
                if prova:
                    materia_norm = normalizar_materia(prova.materia)
                    # Agrupar por matéria normalizada, pegando o resultado mais recente
                    if materia_norm not in provas_aluno or resultado.id > provas_aluno[materia_norm]['resultado_id']:
                        provas_aluno[materia_norm] = {
                            'acertos': resultado.acertos,
                            'resultado_id': resultado.id
                        }
            
            # Buscar notas por matéria normalizada
            nota_portugues = provas_aluno.get('portugues', {}).get('acertos', 0)
            nota_matematica = provas_aluno.get('matematica', {}).get('acertos', 0)
            nota_ciencias = provas_aluno.get('ciencias', {}).get('acertos', 0)
            
            top_alunos_lista.append({
                'idAluno': aluno.idAluno,
                'nome': aluno.nome,
                'turma': aluno.curso,
                'nota_portugues': nota_portugues,
                'nota_matematica': nota_matematica,
                'nota_ciencias': nota_ciencias,
                'media': round(media, 2),
                'foto': aluno.imagem or '/static/img/user.jpg'
            })
        top_alunos = sorted(top_alunos_lista, key=lambda x: x['media'], reverse=True)[:10]

        return {
            'gestor': gestor, # Retornar o objeto gestor para o template
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

    @staticmethod
    def get_aluno_profile_data(db: Session, user_id: int):
        """
        Coleta e processa os dados para o perfil do aluno.
        Agora busca apenas provas das turmas em que o aluno está matriculado.
        """
        from models.aluno_turma import AlunoTurma
        from models.prova_turma import ProvaTurma
        from models.prova_questao import ProvaQuestao
        
        aluno = db.query(Aluno).filter(Aluno.idUser == user_id).first()
        if not aluno:
            return None

        # Buscar turmas do aluno
        turmas_aluno = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno.idAluno,
            AlunoTurma.status == "ativo"
        ).all()
        
        # Se o aluno não está em nenhuma turma, retorna dados vazios
        if not turmas_aluno:
            return {
                "aluno": aluno,
                "materias": [],
                "provas_turmas": [],
                "dados_grafico_pizza": {'labels': [], 'data': [], 'cores': []},
                "dados_grafico_barra": {'labels': [], 'datasets': []}
            }
        
        # Buscar provas das turmas do aluno
        turmas_ids = [at.turma_id for at in turmas_aluno]
        provas_turmas = db.query(ProvaTurma).filter(
            ProvaTurma.turma_id.in_(turmas_ids)
        ).all()
        
        # Organizar provas por matéria
        materias_dict = {}
        for prova_turma in provas_turmas:
            materia = prova_turma.prova.materia
            if materia not in materias_dict:
                materias_dict[materia] = []
            materias_dict[materia].append(prova_turma)
        
        # Preparar dados para o template
        materias_info = []
        provas_turmas_info = []
        
        dados_grafico_pizza = {
            'labels': [],
            'data': [],
            'cores': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
        }
        
        dados_grafico_barra = {
            'labels': [],
            'datasets': [
                {
                    'label': 'Sua média',
                    'data': [],
                    'backgroundColor': '#FF6384'
                },
                {
                    'label': 'Média da turma',
                    'data': [],
                    'backgroundColor': '#36A2EB'
                }
            ]
        }

        # Inicializar max_chart_value antes do loop
        max_chart_value = 10  # Valor padrão
        
        # Processar cada matéria
        for materia_nome, provas_turma_list in materias_dict.items():
            # Pegar a prova mais recente da matéria (ordenar por data de criação da prova)
            provas_turma_list.sort(key=lambda pt: pt.prova.data_criacao, reverse=True)
            prova_turma_mais_recente = provas_turma_list[0]
            prova = prova_turma_mais_recente.prova
            
            # Verificar se o aluno já respondeu
            resultado = db.query(Resultado).filter(
                Resultado.aluno_id == aluno.idAluno,
                Resultado.prova_id == prova.id
            ).first()
            
            # Calcular média da turma (apenas alunos da mesma turma)
            turma_id = prova_turma_mais_recente.turma_id
            media_turma = db.query(func.avg(Resultado.acertos)).join(
                Aluno, Resultado.aluno_id == Aluno.idAluno
            ).join(AlunoTurma, AlunoTurma.aluno_id == Aluno.idAluno).filter(
                AlunoTurma.turma_id == turma_id,
                AlunoTurma.status == "ativo",
                Resultado.prova_id == prova.id
            ).scalar() or 0
            
            if resultado:
                nota = float(resultado.nota)
                status = resultado.situacao
                url_prova = f"/aluno/prova/{prova.id}/consultar"
            else:
                # Verificar se a prova ainda está ativa
                from datetime import datetime
                agora = datetime.now()
                if prova_turma_mais_recente.data_expiracao > agora:
                    nota = None
                    status = "Disponível"
                    url_prova = f"/aluno/prova/{prova.id}/responder"
                else:
                    nota = None
                    status = "Expirada"
                    url_prova = f"/aluno/prova/{prova.id}/consultar"
            
            materias_info.append({
                "nome": materia_nome,
                "nota": nota,
                "status": status,
                "url_prova": url_prova,
                "prova_disponivel": True,
                "turma": prova_turma_mais_recente.turma.nome,
                "professor": prova.professor.nome
            })
            
            # Adicionar dados para gráficos
            dados_grafico_pizza['labels'].append(materia_nome)
            dados_grafico_pizza['data'].append(nota if nota is not None else 0)
            dados_grafico_barra['labels'].append(materia_nome)
            dados_grafico_barra['datasets'][0]['data'].append(nota if nota is not None else 0)
            dados_grafico_barra['datasets'][1]['data'].append(float(media_turma))
            
            # Adicionar informações das provas das turmas
            for prova_turma in provas_turma_list:
                provas_turmas_info.append({
                    "prova": prova_turma.prova,
                    "turma": prova_turma.turma,
                    "professor": prova_turma.professor,
                    "data_inicio": prova_turma.data_inicio,
                    "data_expiracao": prova_turma.data_expiracao,
                    "status": prova_turma.status,
                    "resultado": resultado if resultado and resultado.prova_id == prova_turma.prova.id else None
                })

        # Calcular max_chart_value baseado em todas as provas das turmas do aluno
        if provas_turmas:
            provas_ids = [pt.prova_id for pt in provas_turmas]
            max_questoes = db.query(
                func.count(ProvaQuestao.id)
            ).join(Prova).filter(
                Prova.id.in_(provas_ids)
            ).group_by(Prova.id).order_by(
                func.count(ProvaQuestao.id).desc()
            ).limit(1).scalar() or 0

            if max_questoes > 0:
                max_chart_value = max_questoes
                if max_chart_value % 5 != 0:
                    max_chart_value = ((max_chart_value // 5) + 1) * 5
        
        return {
            "aluno": aluno,
            "materias": materias_info,
            "provas_turmas": provas_turmas_info,
            "dados_grafico_pizza": dados_grafico_pizza,
            "dados_grafico_barra": dados_grafico_barra,
            "maxChartValue": max_chart_value
        }
    
    @staticmethod
    def get_aluno_dashboard_data(db: Session, aluno_id: int):
        """
        Coleta e processa os dados para o dashboard detalhado de um aluno.
        """
        aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
        if not aluno:
            return None # O controller irá lidar com isso

        # Buscar resultados do aluno por disciplina
        resultados_por_disciplina = db.query(
            Prova.materia,
            func.avg(Resultado.acertos).label('media_acertos')
        ).join(Resultado).filter(
            Resultado.aluno_id == aluno_id
        ).group_by(Prova.materia).all()

        # Buscar progressão do aluno
        progressao = db.query(
            Prova.data_criacao,
            Resultado.acertos
        ).join(Resultado).filter(
            Resultado.aluno_id == aluno_id
        ).order_by(Prova.data_criacao).all()

        # Preparar dados para os gráficos
        dados_disciplina = {
            'labels': [r.materia for r in resultados_por_disciplina],
            'data': [float(r.media_acertos) for r in resultados_por_disciplina]
        }

        dados_progressao = {
            'labels': [str(r.data_criacao) for r in progressao],
            'data': [r.acertos for r in progressao]
        }

        return {
            "aluno": aluno,
            "dados_disciplina": dados_disciplina,
            "dados_progressao": dados_progressao
        }
