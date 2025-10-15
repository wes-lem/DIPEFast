import json
from jinja2 import Environment, FileSystemLoader, select_autoescape, DebugUndefined
from fastapi.templating import Jinja2Templates

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
    extensions=["jinja2.ext.debug"],
    undefined=DebugUndefined
)

env.filters['fromjson'] = json.loads 

templates = Jinja2Templates(env=env) 