from sqlalchemy.orm import Session
from models.notificacao_professor import NotificacaoProfessor, TipoNotificacaoProfessor

class NotificacaoProfessorDAO:
    @staticmethod
    def create(db: Session, professor_id: int, tipo: TipoNotificacaoProfessor, 
               titulo: str, mensagem: str):
        """Cria uma nova notificação para professor"""
        notificacao = NotificacaoProfessor(
            professor_id=professor_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem
        )
        db.add(notificacao)
        db.commit()
        db.refresh(notificacao)
        return notificacao

    @staticmethod
    def get_by_professor(db: Session, professor_id: int):
        """Busca notificações de um professor"""
        return db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id
        ).order_by(NotificacaoProfessor.data_criacao.desc()).all()

    @staticmethod
    def get_unread_by_professor(db: Session, professor_id: int):
        """Busca notificações não lidas de um professor"""
        return db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id,
            NotificacaoProfessor.lida == False
        ).order_by(NotificacaoProfessor.data_criacao.desc()).all()

    @staticmethod
    def get_read_by_professor(db: Session, professor_id: int):
        """Busca notificações lidas de um professor"""
        return db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id,
            NotificacaoProfessor.lida == True
        ).order_by(NotificacaoProfessor.data_criacao.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, notificacao_id: int):
        """Marca uma notificação como lida"""
        notificacao = db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.id == notificacao_id
        ).first()
        
        if not notificacao:
            return False
        
        notificacao.lida = True
        db.commit()
        return True

    @staticmethod
    def mark_all_as_read(db: Session, professor_id: int):
        """Marca todas as notificações de um professor como lidas"""
        db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id,
            NotificacaoProfessor.lida == False
        ).update({"lida": True})
        db.commit()
        return True

    @staticmethod
    def get_unread_count(db: Session, professor_id: int):
        """Conta notificações não lidas de um professor"""
        from sqlalchemy import func
        return db.query(func.count(NotificacaoProfessor.id)).filter(
            NotificacaoProfessor.professor_id == professor_id,
            NotificacaoProfessor.lida == False
        ).scalar()

    @staticmethod
    def delete(db: Session, notificacao_id: int):
        """Remove uma notificação"""
        notificacao = db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.id == notificacao_id
        ).first()
        
        if not notificacao:
            return False
        
        db.delete(notificacao)
        db.commit()
        return True

    @staticmethod
    def delete_all_by_professor(db: Session, professor_id: int):
        """Remove todas as notificações de um professor"""
        db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id
        ).delete()
        db.commit()
        return True

    @staticmethod
    def delete_read_by_professor(db: Session, professor_id: int):
        """Remove notificações lidas de um professor"""
        db.query(NotificacaoProfessor).filter(
            NotificacaoProfessor.professor_id == professor_id,
            NotificacaoProfessor.lida == True
        ).delete()
        db.commit()
        return True

    @staticmethod
    def create_prova_expirada_notification(db: Session, professor_id: int, prova_titulo: str, turma_nome: str):
        """Cria notificação de prova expirada"""
        return NotificacaoProfessorDAO.create(
            db=db,
            professor_id=professor_id,
            tipo=TipoNotificacaoProfessor.PROVA_EXPIRADA,
            titulo="Prova Expirada",
            mensagem=f"A prova '{prova_titulo}' da turma '{turma_nome}' expirou. Você pode verificar as respostas dos alunos."
        )

    @staticmethod
    def create_aluno_respondeu_notification(db: Session, professor_id: int, aluno_nome: str, prova_titulo: str):
        """Cria notificação de aluno que respondeu prova"""
        return NotificacaoProfessorDAO.create(
            db=db,
            professor_id=professor_id,
            tipo=TipoNotificacaoProfessor.ALUNO_RESPONDEU,
            titulo="Aluno Respondeu Prova",
            mensagem=f"O aluno '{aluno_nome}' respondeu a prova '{prova_titulo}'."
        )

    @staticmethod
    def create_turma_criada_notification(db: Session, professor_id: int, turma_nome: str, codigo: str):
        """Cria notificação de turma criada"""
        return NotificacaoProfessorDAO.create(
            db=db,
            professor_id=professor_id,
            tipo=TipoNotificacaoProfessor.TURMA_CRIADA,
            titulo="Turma Criada",
            mensagem=f"A turma '{turma_nome}' foi criada com sucesso. Código: {codigo}"
        )

    @staticmethod
    def create_prova_criada_notification(db: Session, professor_id: int, prova_titulo: str):
        """Cria notificação de prova criada"""
        return NotificacaoProfessorDAO.create(
            db=db,
            professor_id=professor_id,
            tipo=TipoNotificacaoProfessor.PROVA_CRIADA,
            titulo="Prova Criada",
            mensagem=f"A prova '{prova_titulo}' foi criada com sucesso."
        )
