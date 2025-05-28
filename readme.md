# DIPE - Sistema de Diagnóstico e Intervenção Pedagógica e Educacional

## 📌 Visão Geral
O DIPE é um sistema web desenvolvido em FastAPI e tecnologias modernas para o acompanhamento pedagógico de alunos, permitindo coleta, organização e análise de dados acadêmicos e socioeconômicos. O sistema foi projetado para identificar dificuldades individuais e coletivas, proporcionando uma gestão eficaz de intervenções pedagógicas.

## ✨ Funcionalidades Principais

### 👨‍🎓 Área do Aluno
- Cadastro individual com informações pessoais e socioeconômicas
- Realização de provas diagnósticas online
- Visualização de desempenho por disciplina
- Acompanhamento da progressão individual
- Atualização de dados pessoais

### 👨‍🏫 Área do Gestor
- Dashboard analítico com métricas de desempenho
- Visualização de desempenho por disciplina
- Análise de distribuição de notas
- Comparação entre turmas
- Acompanhamento da progressão dos alunos
- Análise do perfil dos alunos
- Monitoramento da taxa de participação

## 🛠 Tecnologias Utilizadas

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy (ORM)
- Uvicorn (ASGI server)

### Frontend
- Jinja2 (templates)
- Bootstrap 5
- Chart.js (gráficos)
- Vanilla JavaScript

### Banco de Dados
- MySQL

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior
- MySQL

### Instalação
1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Configure o banco de dados MySQL
4. Execute o servidor:
```bash
cd "C:\Users\Weslem\Desktop\Versões DIPE\DIPEFast"
.\venv\Scripts\activate
uvicorn main:app --reload
```

## 📊 Estrutura do Projeto
```
DIPE/
├── controllers/          # Controladores da aplicação
│   ├── aluno_controller.py    # Rotas do aluno
│   ├── gestor_controller.py   # Rotas do gestor
│   ├── prova_controller.py    # Rotas das provas
│   ├── questao_controller.py  # Rotas das questões
│   ├── resposta_controller.py # Rotas das respostas
│   └── usuario_controller.py  # Rotas de usuários
├── dao/                  # Data Access Objects
│   ├── aluno_dao.py     # Operações com alunos
│   ├── database.py      # Configuração do banco
│   └── usuario_dao.py   # Operações com usuários
├── models/              # Modelos de dados
│   ├── aluno.py        # Modelo de aluno
│   ├── prova.py        # Modelo de prova
│   ├── questao.py      # Modelo de questão
│   ├── resposta.py     # Modelo de resposta
│   ├── resultado.py    # Modelo de resultado
│   └── usuario.py      # Modelo de usuário
├── templates/           # Templates HTML
│   ├── static/         # Arquivos estáticos
│   │   ├── css/        # Estilos CSS
│   │   ├── js/         # Scripts JavaScript
│   │   ├── img/        # Imagens
│   │   └── uploads/    # Uploads de imagens
│   ├── cadastro.html           # Página de cadastro
│   ├── cadastro_aluno.html     # Cadastro de aluno
│   ├── cadastro_prova.html     # Cadastro de prova
│   ├── dashboard.html          # Dashboard do gestor
│   ├── dashboard_aluno.html    # Dashboard do aluno
│   ├── dashboard_gestor.html   # Dashboard do gestor
│   ├── gestor_alunos.html      # Lista de alunos
│   ├── gestor_cadastro.html    # Cadastro pelo gestor
│   ├── index.html             # Página inicial
│   ├── login.html             # Página de login
│   └── perfil.html            # Perfil do aluno
├── main.py              # Ponto de entrada
└── requirements.txt     # Dependências do projeto
```

## 📄 Licença
Este projeto é de uso acadêmico, sem fins lucrativos.

## ✉️ Equipe de Desenvolvimento
Desenvolvido por Weslem Rodrigues e Iasmin Azevedo, como projeto de Arquitetura de Sistemas do IFCE - Campus Boa Viagem, demonstrando a aplicação de padrões arquiteturais modernos em soluções educacionais.
