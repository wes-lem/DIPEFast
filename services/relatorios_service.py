from sqlalchemy.orm import Session
from sqlalchemy import func
from models.aluno import Aluno
from models.prova import Prova
from models.resultado import Resultado


class RelatoriosService:
	@staticmethod
	def get_professor_report_data(db: Session, professor_id: int):
		provas = db.query(Prova).filter(Prova.professor_id == professor_id).all()
		provas_labels = [p.titulo for p in provas]
		provas_medias = []
		provas_participacao = []
		for p in provas:
			media = db.query(func.avg(Resultado.acertos)).filter(Resultado.prova_id == p.id).scalar() or 0
			participantes = db.query(func.count(Resultado.id)).filter(Resultado.prova_id == p.id).scalar() or 0
			provas_medias.append(float(media))
			provas_participacao.append(int(participantes))

		materias = db.query(Prova.materia).filter(Prova.professor_id == professor_id).distinct().all()
		materias_labels = [m[0] for m in materias]
		materias_medias = []
		for m in materias_labels:
			media_materia = (
				db.query(func.avg(Resultado.acertos))
				.join(Prova, Prova.id == Resultado.prova_id)
				.filter(Prova.professor_id == professor_id, Prova.materia == m)
				.scalar()
				or 0
			)
			materias_medias.append(float(media_materia))

		return {
			"provas": {"labels": provas_labels, "medias": provas_medias, "participacao": provas_participacao},
			"materias": {"labels": materias_labels, "medias": materias_medias},
		}

	@staticmethod
	def get_gestor_report_data(db: Session):
		materias = db.query(Prova.materia).distinct().all()
		materias_labels = [m[0] for m in materias]
		materias_medias = []
		for m in materias_labels:
			media_materia = (
				db.query(func.avg(Resultado.acertos))
				.join(Prova, Prova.id == Resultado.prova_id)
				.filter(Prova.materia == m)
				.scalar()
				or 0
			)
			materias_medias.append(float(media_materia))

		cursos = db.query(Aluno.curso).distinct().all()
		cursos_labels = [c[0] for c in cursos]
		cursos_medias = []
		for c in cursos_labels:
			media_curso = (
				db.query(func.avg(Resultado.acertos))
				.join(Aluno, Aluno.idAluno == Resultado.aluno_id)
				.filter(Aluno.curso == c)
				.scalar()
				or 0
			)
			cursos_medias.append(float(media_curso))

		participacao_total_alunos = db.query(func.count(Aluno.idAluno)).scalar() or 0
		participaram = db.query(Resultado.aluno_id).distinct().count()
		nao_participaram = max(0, participacao_total_alunos - participaram)

		return {
			"materias": {"labels": materias_labels, "medias": materias_medias},
			"cursos": {"labels": cursos_labels, "medias": cursos_medias},
			"participacao": {"labels": ["Participaram", "Não participaram"], "data": [participaram, nao_participaram]},
		}


