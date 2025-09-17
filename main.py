from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from controllers.usuario_controller import router as usuario_router
from controllers.aluno_controller import router as aluno_router
from controllers.prova_controller import router as prova_router
from controllers.gestor_controller import router as gestor_router
from controllers.formulario_controller import router as formulario_router
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.exceptions import HTTPException
import os
import uvicorn
from app_config import templates
from dao.database import engine, Base

from dao.cadastrarGestor import criar_gestor_padrao

Base.metadata.create_all(bind=engine)

criar_gestor_padrao()

app = FastAPI()

app.mount("/static", StaticFiles(directory="templates/static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("aluno/login.html", {"request": request})

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manipulador global que usa o cabeçalho 'Referer' para criar
    um link de "voltar para a página anterior".
    """
    
    referer_url = request.headers.get("referer")
    back_url = referer_url or "/" 
    
    return templates.TemplateResponse(
        "erro.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "back_url": back_url
        },
        status_code=exc.status_code
    )

# Inclui as rotas de todos os controllers
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(prova_router)
app.include_router(gestor_router)
app.include_router(formulario_router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )