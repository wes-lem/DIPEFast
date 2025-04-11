from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from dao.database import get_db
from models.resposta import Resposta
from models.questao import Questao
from models.aluno import Aluno
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/perfil/{aluno_id}/resultado")
def resultado_provas(request: Request, aluno_id: int, db: Session = Depends(get_db)):
    respostas = db.query(Resposta).filter(Resposta.aluno_id == aluno_id).all()
    
    pontuacao = {"Português": 0, "Matemática": 0, "Ciências": 0}
    total_questoes = {"Português": 0, "Matemática": 0, "Ciências": 0}

    for resposta in respostas:
        questao = db.query(Questao).filter(Questao.id == resposta.questao_id).first()
        if questao:
            total_questoes[questao.materia] += 1
            if resposta.resposta == questao.resposta_correta:
                pontuacao[questao.materia] += 1

    situacoes = {}
    for materia, acertos in pontuacao.items():
        if acertos <= 5:
            situacoes[materia] = "Insuficiente"
        elif acertos <= 10:
            situacoes[materia] = "Regular"
        else:
            situacoes[materia] = "Suficiente"

    return templates.TemplateResponse(
        "resultado.html", {"request": request, "pontuacao": pontuacao, "situacoes": situacoes}
    )
