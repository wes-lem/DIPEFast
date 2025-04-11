from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from dao.database import get_db
from models.questao import Questao
from dao.questao_dao import QuestaoDAO
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/provas/{prova_id}/questoes")
def listar_questoes(request: Request, prova_id: int, db: Session = Depends(get_db)):
    questoes = db.query(Questao).filter(Questao.prova_id == prova_id).all()
    return templates.TemplateResponse("listar_questoes.html", {"request": request, "questoes": questoes})

@router.post("/provas/{prova_id}/questoes")
def adicionar_questao(
    prova_id: int,
    enunciado: str = Form(...),
    alternativa_a: str = Form(...),
    alternativa_b: str = Form(...),
    alternativa_c: str = Form(...),
    alternativa_d: str = Form(...),
    alternativa_e: str = Form(...),
    resposta_correta: str = Form(...),
    db: Session = Depends(get_db),
):
    QuestaoDAO.create(
        db, prova_id, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, resposta_correta
    )
    return RedirectResponse(url=f"/provas/{prova_id}/questoes", status_code=303)
