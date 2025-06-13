import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.templating import Jinja2Templates

# 1. Crie o ambiente Jinja2
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"])
)

# 2. Registre o filtro 'fromjson' no ambiente
env.filters['fromjson'] = json.loads 

# 3. Inicialize Jinja2Templates PASSANDO o ambiente personalizado
templates = Jinja2Templates(env=env) 