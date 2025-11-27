"""
Serviço para análise e agregação de dados de formulários dinâmicos.
Gera dados para gráficos Chart.js de perguntas de escolha única e múltipla escolha.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.resposta_formulario import RespostaFormulario
from models.pergunta_formulario import PerguntaFormulario
import json
from collections import Counter
from typing import Dict, List, Any

class FormularioAnalyticsService:
    """Serviço para análise de formulários e geração de dados para gráficos."""
    
    @staticmethod
    def get_formulario_analytics(db: Session, formulario_id: int) -> Dict[str, Any]:
        """
        Retorna todos os dados analíticos de um formulário.
        Inclui estatísticas gerais e dados para gráficos de cada pergunta.
        """
        from dao.formulario_dao import FormularioDAO
        from dao.resposta_formulario_dao import RespostaFormularioDAO
        
        formulario = FormularioDAO.get_by_id(db, formulario_id)
        if not formulario:
            return None
        
        # Estatísticas gerais
        total_respondedores = RespostaFormularioDAO.get_total_respondedores_by_formulario(db, formulario_id)
        total_respostas = RespostaFormularioDAO.get_estatisticas_formulario(db, formulario_id)
        
        # Buscar todas as perguntas do formulário
        from dao.pergunta_formulario_dao import PerguntaFormularioDAO
        perguntas = PerguntaFormularioDAO.get_by_formulario(db, formulario_id)
        
        # Gerar dados para gráficos de cada pergunta
        graficos_perguntas = []
        for pergunta in perguntas:
            grafico_data = FormularioAnalyticsService._gerar_grafico_pergunta(
                db, formulario_id, pergunta
            )
            if grafico_data:
                graficos_perguntas.append(grafico_data)
        
        return {
            "formulario": formulario,
            "total_respondedores": total_respondedores,
            "total_respostas": total_respostas.get("total_respostas", 0),
            "graficos_perguntas": graficos_perguntas,
            "perguntas": perguntas
        }
    
    @staticmethod
    def _gerar_grafico_pergunta(
        db: Session, 
        formulario_id: int, 
        pergunta: PerguntaFormulario
    ) -> Dict[str, Any]:
        """
        Gera dados para gráfico de uma pergunta específica.
        Retorna None se a pergunta não for de escolha única ou múltipla escolha.
        """
        if pergunta.tipo_pergunta not in ['escolha_unica', 'selecao_unica', 'sim_nao', 'multipla_escolha']:
            return None
        
        # Buscar todas as respostas para esta pergunta
        respostas = db.query(RespostaFormulario).filter(
            RespostaFormulario.formulario_id == formulario_id,
            RespostaFormulario.pergunta_id == pergunta.id
        ).all()
        
        if not respostas:
            return {
                "pergunta_id": pergunta.id,
                "enunciado": pergunta.enunciado,
                "tipo": pergunta.tipo_pergunta,
                "tem_respostas": False,
                "grafico": None
            }
        
        # Processar opções da pergunta
        opcoes_pergunta = []
        if pergunta.opcoes:
            try:
                opcoes_pergunta = json.loads(pergunta.opcoes)
            except:
                opcoes_pergunta = []
        
        # Agregar respostas
        if pergunta.tipo_pergunta in ['escolha_unica', 'selecao_unica', 'sim_nao']:
            # Para escolha única, as respostas podem estar em resposta_texto ou resposta_opcoes
            contagem = Counter()
            for resposta in respostas:
                opcao_selecionada = None
                
                # Primeiro tentar resposta_texto (formato mais comum)
                if resposta.resposta_texto:
                    opcao_selecionada = resposta.resposta_texto.strip()
                
                # Se não tiver em texto, tentar resposta_opcoes
                elif resposta.resposta_opcoes:
                    try:
                        opcao_parsed = json.loads(resposta.resposta_opcoes)
                        if isinstance(opcao_parsed, list) and len(opcao_parsed) > 0:
                            opcao_selecionada = str(opcao_parsed[0]).strip()
                        elif isinstance(opcao_parsed, str):
                            opcao_selecionada = opcao_parsed.strip()
                    except (json.JSONDecodeError, TypeError):
                        # Se não for JSON válido, tratar como string direta
                        opcao_selecionada = str(resposta.resposta_opcoes).strip()
                
                if opcao_selecionada:
                    contagem[opcao_selecionada] += 1
            
            # Preparar dados para gráfico de pizza
            labels = []
            data = []
            
            # Se houver opções definidas na pergunta, usar essas como base
            if opcoes_pergunta:
                cores = FormularioAnalyticsService._gerar_cores(len(opcoes_pergunta))
                # Incluir todas as opções, mesmo as não selecionadas
                for opcao in opcoes_pergunta:
                    labels.append(opcao)
                    data.append(contagem.get(opcao, 0))
                
                # Incluir opções que foram selecionadas mas não estão na lista original
                for opcao, count in contagem.items():
                    if opcao not in labels:
                        labels.append(opcao)
                        data.append(count)
                        cores.append('#CCCCCC')  # Cor neutra para opções não listadas
            else:
                # Se não houver opções definidas, usar apenas as respostas coletadas
                cores = FormularioAnalyticsService._gerar_cores(len(contagem))
                for opcao, count in contagem.items():
                    labels.append(opcao)
                    data.append(count)
            
            return {
                "pergunta_id": pergunta.id,
                "enunciado": pergunta.enunciado,
                "tipo": pergunta.tipo_pergunta,
                "tipo_grafico": "pie",  # Pizza para escolha única
                "tem_respostas": True,
                "total_respostas": len(respostas),
                "grafico": {
                    "labels": labels,
                    "data": data,
                    "cores": cores[:len(labels)]
                }
            }
        
        elif pergunta.tipo_pergunta == 'multipla_escolha':
            # Para múltipla escolha, resposta_opcoes contém uma lista de opções
            contagem = Counter()
            for resposta in respostas:
                if resposta.resposta_opcoes:
                    try:
                        opcoes_selecionadas = json.loads(resposta.resposta_opcoes)
                        if isinstance(opcoes_selecionadas, list):
                            for opcao in opcoes_selecionadas:
                                contagem[str(opcao)] += 1
                    except (json.JSONDecodeError, TypeError):
                        # Se não for JSON válido, tratar como string única
                        contagem[str(resposta.resposta_opcoes)] += 1
            
            # Preparar dados para gráfico de barras (melhor para múltipla escolha)
            labels = []
            data = []
            cores = FormularioAnalyticsService._gerar_cores(len(opcoes_pergunta))
            
            # Incluir todas as opções
            for opcao in opcoes_pergunta:
                labels.append(opcao)
                data.append(contagem.get(opcao, 0))
            
            # Incluir opções não listadas
            for opcao, count in contagem.items():
                if opcao not in labels:
                    labels.append(opcao)
                    data.append(count)
                    cores.append('#CCCCCC')
            
            return {
                "pergunta_id": pergunta.id,
                "enunciado": pergunta.enunciado,
                "tipo": "multipla_escolha",
                "tipo_grafico": "bar",  # Barras para múltipla escolha
                "tem_respostas": True,
                "total_respostas": len(respostas),
                "grafico": {
                    "labels": labels,
                    "data": data,
                    "cores": cores[:len(labels)]
                }
            }
        
        return None
    
    @staticmethod
    def _gerar_cores(quantidade: int) -> List[str]:
        """Gera uma lista de cores para os gráficos."""
        cores_base = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
            '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
        ]
        
        # Repetir cores se necessário
        if quantidade <= len(cores_base):
            return cores_base[:quantidade]
        
        # Gerar cores adicionais interpolando
        cores = cores_base.copy()
        while len(cores) < quantidade:
            cores.extend(cores_base)
        
        return cores[:quantidade]
    
    @staticmethod
    def get_respostas_texto_agregadas(
        db: Session, 
        formulario_id: int, 
        pergunta_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retorna respostas de texto para uma pergunta (para exibição em lista).
        """
        respostas = db.query(RespostaFormulario).filter(
            RespostaFormulario.formulario_id == formulario_id,
            RespostaFormulario.pergunta_id == pergunta_id
        ).all()
        
        respostas_texto = []
        for resposta in respostas:
            if resposta.resposta_texto:
                respostas_texto.append({
                    "aluno_id": resposta.aluno_id,
                    "aluno_nome": resposta.aluno.nome if resposta.aluno else "Aluno",
                    "texto": resposta.resposta_texto,
                    "data_resposta": resposta.data_resposta
                })
        
        return respostas_texto

