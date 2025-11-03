from sqlalchemy.orm import Session
from sqlalchemy import desc, and_ # Adicionado 'and_' para usar em filtros múltiplos
from models.notificacao import Notificacao
from models.aluno import Aluno
from models.formulario import Formulario
from dao.resposta_formulario_dao import RespostaFormularioDAO

class NotificacaoDAO:
    @staticmethod
    def create_notificacao(db: Session, aluno_id: int, titulo: str, mensagem: str = None, link: str = None):
        """Cria uma nova notificação para um aluno."""
        # Se você quiser que a notificação seja LIDA por padrão, mude 'lida=False' para 'lida=True'.
        # Pelo contexto, é uma nova notificação, então deve ser não lida.
        nova_notificacao = Notificacao(
            aluno_id=aluno_id,
            titulo=titulo,
            mensagem=mensagem,
            link=link,
            lida=False
        )
        db.add(nova_notificacao)
        db.commit()
        db.refresh(nova_notificacao)
        return nova_notificacao

    @staticmethod
    def get_notificacoes_by_aluno(db: Session, aluno_id: int, lida: bool = None, limit: int = None):
        """
        Retorna notificações para um aluno, opcionalmente filtrando por 'lida'
        e limitando a quantidade. Valida se os formulários ainda existem e são relevantes para o aluno.
        """
        from dao.formulario_dao import FormularioDAO
        import re
        
        query = db.query(Notificacao).filter(Notificacao.aluno_id == aluno_id)
        if lida is not None: # Se 'lida' for True ou False, aplica o filtro
            query = query.filter(Notificacao.lida == lida)
        
        query = query.order_by(desc(Notificacao.data_criacao)) # Notificações mais recentes primeiro

        if limit:
            query = query.limit(limit)
        
        notificacoes = query.all()
        
        # Filtrar notificações válidas: verificar se formulário existe e é relevante para o aluno
        notificacoes_validas = []
        formularios_validos = FormularioDAO.get_for_aluno(db, aluno_id)
        formulario_ids_validos = {f.id for f in formularios_validos}
        
        for notif in notificacoes:
            # Extrair formulario_id do link se existir
            formulario_id = None
            if notif.link and "/aluno/formularios/" in notif.link:
                try:
                    match = re.search(r'/aluno/formularios/(\d+)', notif.link)
                    if match:
                        formulario_id = int(match.group(1))
                except:
                    pass
            
            # Se não é notificação de formulário ou se o formulário existe e é válido para o aluno
            if not formulario_id or formulario_id in formulario_ids_validos:
                notificacoes_validas.append(notif)
            else:
                # Remover notificação de formulário que não existe mais ou não é relevante
                db.delete(notif)
        
        db.commit()
        return notificacoes_validas

    @staticmethod
    def get_notificacao_by_id(db: Session, notificacao_id: int):
        """Retorna uma notificação específica pelo ID."""
        return db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()

    @staticmethod
    def marcar_notificacao_como_lida(db: Session, aluno_id: int, notificacao_id: int = None, link: str = None):
        """
        Marca uma ou mais notificações como lidas.
        Pode marcar uma específica por ID ou todas relacionadas a um link/formulário.
        """
        if notificacao_id:
            notificacao = db.query(Notificacao).filter(
                Notificacao.id == notificacao_id,
                Notificacao.aluno_id == aluno_id
            ).first()
            if notificacao:
                notificacao.lida = True
                db.commit()
                db.refresh(notificacao)
                return True
        elif link: 
            
            notificacoes = db.query(Notificacao).filter(
                and_(
                    Notificacao.aluno_id == aluno_id,
                    Notificacao.link == link,
                    Notificacao.lida == False
                )
            ).all()
            if notificacoes:
                for notif in notificacoes:
                    notif.lida = True
                db.commit()
                return True
        return False

    @staticmethod
    def marcar_todas_notificacoes_como_lidas(db: Session, aluno_id: int):
        """Marca todas as notificações não lidas de um aluno como lidas."""
        db.query(Notificacao).filter(
            Notificacao.aluno_id == aluno_id,
            Notificacao.lida == False
        ).update({"lida": True}, synchronize_session="fetch")
        db.commit()
        return True

    @staticmethod
    def delete_notificacao(db: Session, notificacao_id: int):
        """Deleta uma notificação pelo ID."""
        notificacao = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
        if notificacao:
            db.delete(notificacao)
            db.commit()
            return True
        return False
    
    @staticmethod
    def criar_notificacao_para_novo_formulario(db: Session, aluno_id: int, formulario_id: int, titulo_formulario: str):
        """Cria uma notificação específica para um novo formulário, para um aluno."""
        return NotificacaoDAO.create_notificacao( # Chamando o método 'create_notificacao' para reutilizar
            db=db,
            aluno_id=aluno_id,
            titulo=f"Novo Formulário: {titulo_formulario}",
            mensagem=f"Há um novo formulário '{titulo_formulario}' disponível para você responder. Clique para acessá-lo.",
            link=f"/aluno/formularios/{formulario_id}"
        )

    @staticmethod
    def verificar_formularios_nao_respondidos(db: Session):
        """Verifica formulários não respondidos e cria notificações para os alunos.
        Usa o método get_for_aluno para garantir que apenas formulários relevantes sejam considerados."""
        from dao.formulario_dao import FormularioDAO
        
        # Busca todos os alunos
        alunos = db.query(Aluno).all()
        
        for aluno in alunos:
            # Busca apenas formulários relevantes para este aluno (filtrados por turma/campus/curso)
            formularios = FormularioDAO.get_for_aluno(db, aluno.idAluno)
            
            for formulario in formularios:
                # Verifica se o aluno já respondeu este formulário
                if not RespostaFormularioDAO.has_aluno_responded_formulario(db, aluno.idAluno, formulario.id):
                    # Verifica se já existe uma notificação não lida para este formulário
                    notificacao_existente = db.query(Notificacao).filter(
                        and_(
                            Notificacao.aluno_id == aluno.idAluno,
                            Notificacao.link == f"/aluno/formularios/{formulario.id}",
                            Notificacao.lida == False
                        )
                    ).first()
                    
                    # Se não existe notificação ou se a notificação existente está lida, cria uma nova
                    if not notificacao_existente:
                        # Remove qualquer notificação antiga (lida ou não) para este formulário
                        db.query(Notificacao).filter(
                            and_(
                                Notificacao.aluno_id == aluno.idAluno,
                                Notificacao.link == f"/aluno/formularios/{formulario.id}"
                            )
                        ).delete()
                        
                        # Cria uma nova notificação
                        NotificacaoDAO.create_notificacao(
                            db=db,
                            aluno_id=aluno.idAluno,
                            titulo=f"Formulário Pendente: {formulario.titulo}",
                            mensagem=f"Você ainda não respondeu o formulário '{formulario.titulo}'. Clique para respondê-lo.",
                            link=f"/aluno/formularios/{formulario.id}"
                        )
                        db.commit()