from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from controllers.usuario_controller import router as usuario_router
from controllers.aluno_controller import router as aluno_router
from controllers.prova_controller import router as prova_router
from controllers.gestor_controller import router as gestor_router
import os
import uvicorn

app = FastAPI()

# Configuração do Jinja2 para templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("aluno/login.html", {"request": request})

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# Inclui as rotas do controller de usuários
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(prova_router)
app.include_router(gestor_router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)