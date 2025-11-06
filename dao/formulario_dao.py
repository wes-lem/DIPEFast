from sqlalchemy.orm import Session
from models.formulario import Formulario
from models.pergunta_formulario import PerguntaFormulario
import json

class FormularioDAO:
    @staticmethod
    def create(db: Session, titulo: str, descricao: str, turma_id: int = None, campus_id: int = None, curso: str = None):
        formulario = Formulario(
            titulo=titulo,
            descricao=descricao,
            turma_id=turma_id,
            campus_id=campus_id,
            curso=curso
        )
        db.add(formulario)
        db.commit()
        db.refresh(formulario)
        return formulario

    @staticmethod
    def get_by_id(db: Session, formulario_id: int):
        return db.query(Formulario).filter(Formulario.id == formulario_id).first()

    @staticmethod
    def get_all(db: Session):
        return db.query(Formulario).all()

    @staticmethod
    def get_active(db: Session):
        return db.query(Formulario).all()
    
    @staticmethod
    def get_for_aluno(db: Session, aluno_id: int):
        """Busca formulários disponíveis para um aluno específico baseado em turma/campus/curso"""
        from models.aluno import Aluno
        from models.aluno_turma import AlunoTurma
        
        aluno = db.query(Aluno).filter(Aluno.idAluno == aluno_id).first()
        if not aluno:
            return []
        
        # Buscar turmas do aluno
        aluno_turmas = db.query(AlunoTurma).filter(
            AlunoTurma.aluno_id == aluno_id,
            AlunoTurma.status == 'ativo'
        ).all()
        turma_ids = [at.turma_id for at in aluno_turmas]
        
        # Buscar campus das turmas do aluno
        campus_ids = []
        if turma_ids:
            from models.turma import Turma
            turmas = db.query(Turma).filter(Turma.id.in_(turma_ids)).all()
            campus_ids = [t.campus_id for t in turmas]
        
        # Buscar formulários que:
        # 1. Não têm nenhum filtro (turma_id, campus_id, curso são None) - para todos
        # 2. São direcionados à turma do aluno
        # 3. São direcionados ao campus do aluno
        # 4. São direcionados ao curso do aluno
        from sqlalchemy import or_, and_
        
        conditions = []
        
        # Formulários sem filtro (para todos)
        conditions.append(
            and_(
                Formulario.turma_id.is_(None),
                Formulario.campus_id.is_(None),
                Formulario.curso.is_(None)
            )
        )
        
        # Formulários direcionados à turma do aluno
        if turma_ids:
            conditions.append(Formulario.turma_id.in_(turma_ids))
        
        # Formulários direcionados ao campus do aluno
        if campus_ids:
            conditions.append(Formulario.campus_id.in_(campus_ids))
        
        # Formulários direcionados ao curso do aluno
        if aluno.curso:
            conditions.append(Formulario.curso == aluno.curso)
        
        query = db.query(Formulario).filter(or_(*conditions))
        
        return query.all()

    @staticmethod
    def add_pergunta(
        db: Session, 
        formulario_id: int, 
        tipo_pergunta: str, 
        enunciado: str, 
        opcoes: list = None
    ):
        pergunta = PerguntaFormulario(
            formulario_id=formulario_id,
            tipo_pergunta=tipo_pergunta,
            enunciado=enunciado,
            opcoes=json.dumps(opcoes) if opcoes else None
        )
        db.add(pergunta)
        db.commit()
        db.refresh(pergunta)
        return pergunta

    @staticmethod
    def get_perguntas(db: Session, formulario_id: int):
        return db.query(PerguntaFormulario).filter(
            PerguntaFormulario.formulario_id == formulario_id
        ).order_by(PerguntaFormulario.ordem).all()

    @staticmethod
    def delete(db: Session, formulario_id: int):
        formulario = db.query(Formulario).filter(Formulario.id == formulario_id).first()
        if formulario:
            db.delete(formulario)
            db.commit()
            print("Formulario deletado com sucesso")
            return True
        return False 