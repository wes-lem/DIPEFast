from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, distinct, and_
from models.aluno import Aluno
from models.prova import Prova
from models.resultado import Resultado
from models.gestor import Gestor # Para buscar dados do gestor, se necessário

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
        total_provas = db.query(func.count(distinct(Resultado.prova_id))).scalar() or 0
        
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

        # Desempenho por disciplina
        desempenho_disciplina = {
            'labels': ['Português', 'Matemática', 'Ciências'],
            'data': [
                float(db.query(func.avg(Resultado.acertos)).join(Prova, Resultado.prova_id == Prova.id).filter(Prova.materia == "Português").scalar() or 0),
                float(db.query(func.avg(Resultado.acertos)).join(Prova, Resultado.prova_id == Prova.id).filter(Prova.materia == "Matemática").scalar() or 0),
                float(db.query(func.avg(Resultado.acertos)).join(Prova, Resultado.prova_id == Prova.id).filter(Prova.materia == "Ciências").scalar() or 0)
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
            top_alunos_lista.append({
                'nome': aluno.nome,
                'turma': aluno.curso,
                'nota_portugues': next((r.acertos for r in resultados_aluno if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Português').first()), 0),
                'nota_matematica': next((r.acertos for r in resultados_aluno if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Matemática').first()), 0),
                'nota_ciencias': next((r.acertos for r in resultados_aluno if db.query(Prova).filter(Prova.id == r.prova_id, Prova.materia == 'Ciências').first()), 0),
                'media': round(media, 2),
                'foto': aluno.imagem or '/static/img/user.png'
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
        """
        aluno = db.query(Aluno).filter(Aluno.idUser == user_id).first()
        if not aluno:
            return None # Ou raise HTTPException para o controller tratar

        materias_fixas = ["Português", "Matemática", "Ciências"]
        materias_info = [] # Renomeado para evitar conflito com a variável global 'materias'
        
        dados_grafico_pizza = {
            'labels': materias_fixas,
            'data': [],
            'cores': ['#FF6384', '#36A2EB', '#FFCE56']
        }
        
        dados_grafico_barra = {
            'labels': materias_fixas,
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
                },
                {
                    'label': 'Média geral',
                    'data': [],
                    'backgroundColor': '#FFCE56'
                }
            ]
        }

        for materia_nome in materias_fixas:
            prova = db.query(Prova).filter(Prova.materia == materia_nome).first()
            prova_disponivel = prova is not None 

            if prova:
                resultado = db.query(Resultado).filter(
                    Resultado.aluno_id == aluno.idAluno,
                    Resultado.prova_id == prova.id
                ).first()
                
                media_turma = db.query(func.avg(Resultado.acertos)).join(
                    Aluno, Resultado.aluno_id == Aluno.idAluno
                ).filter(
                    Aluno.curso == aluno.curso,
                    Resultado.prova_id == prova.id
                ).scalar() or 0

                media_geral = db.query(func.avg(Resultado.acertos)).filter(
                    Resultado.prova_id == prova.id
                ).scalar() or 0
                
                if resultado:
                    nota = float(resultado.acertos)
                    status = resultado.situacao
                    url_prova = f"/prova/{prova.id}/resultado-detalhado"
                else:
                    nota = None
                    status = "Não realizada"
                    url_prova = f"/prova/{prova.id}"
                
                dados_grafico_pizza['data'].append(nota if nota is not None else 0)
                dados_grafico_barra['datasets'][0]['data'].append(nota if nota is not None else 0)
                dados_grafico_barra['datasets'][1]['data'].append(float(media_turma))
                dados_grafico_barra['datasets'][2]['data'].append(float(media_geral))
            else:
                nota = None
                status = "Ainda não há provas disponíveis"
                url_prova = "#"
                dados_grafico_pizza['data'].append(0)
                dados_grafico_barra['datasets'][0]['data'].append(0)
                dados_grafico_barra['datasets'][1]['data'].append(0)
                dados_grafico_barra['datasets'][2]['data'].append(0)

            materias_info.append({
                "nome": materia_nome,
                "nota": nota,
                "status": status,
                "url_prova": url_prova,
                "prova_disponivel": prova_disponivel
            })
        
        return {
            "aluno": aluno,
            "materias": materias_info,
            "dados_grafico_pizza": dados_grafico_pizza,
            "dados_grafico_barra": dados_grafico_barra
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
