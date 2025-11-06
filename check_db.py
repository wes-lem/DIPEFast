from dao.database import engine
from sqlalchemy import inspect
from models.formulario import Formulario
from models.pergunta_formulario import PerguntaFormulario
from models.resposta_formulario import RespostaFormulario
from models.notificacao import Notificacao

inspector = inspect(engine)

# Verificar tabelas
print("Tabelas existentes:", inspector.get_table_names())

# Verificar colunas da tabela formularios
print("\nColunas da tabela formularios:")
for col in inspector.get_columns('formularios'):
    print(f"- {col['name']}: {col['type']}")

# Verificar colunas da tabela perguntas_formulario
print("\nColunas da tabela perguntas_formulario:")
for col in inspector.get_columns('perguntas_formulario'):
    print(f"- {col['name']}: {col['type']}")

# Verificar colunas da tabela respostas_formulario
print("\nColunas da tabela respostas_formulario:")
for col in inspector.get_columns('respostas_formulario'):
    print(f"- {col['name']}: {col['type']}")

# Verificar colunas da tabela notificacoes
print("\nColunas da tabela notificacoes:")
for col in inspector.get_columns('notificacoes'):
    print(f"- {col['name']}: {col['type']}") 