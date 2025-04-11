# DIPEFast - Sistema de Diagnóstico e Intervenção Pedagógica e Educacional

## 📌 Visão Geral
O DIPEFast é um sistema web desenvolvido em FastAPI e tecnologias modernas para o acompanhamento pedagógico de alunos, permitindo coleta, organização e análise de dados acadêmicos e socioeconômicos. O sistema foi projetado para identificar dificuldades individuais e coletivas, proporcionando uma gestão eficaz de intervenções pedagógicas.

## ✨ Funcionalidades Principais

### 👨‍🎓 Área do Aluno
- Cadastro individual com informações pessoais e socioeconômicas  
- Realização de provas diagnósticas online  
- Feedback imediato sobre desempenho  
- Acesso privado ao histórico acadêmico  
- Atualização de dados pessoais  

### 👨‍🏫 Área do Gestor
- Dashboard analítico com métricas de desempenho  
- Filtros avançados por turma, ano e curso  
- Registro de intervenções pedagógicas  
- Exportação de relatórios em PDF/Excel  
- Acompanhamento de progresso dos alunos  

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
- PostgreSQL (produção)  
- SQLite (desenvolvimento)  

### Segurança
- Autenticação JWT  
- Criptografia AES-256  
- Proteção LGPD  

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior  

## 📊 Estrutura do Projeto
DIPEFast/
├── alembic/              # Migrações do banco de dados
├── app/
│   ├── core/             # Configurações principais
│   ├── db/               # Conexão com banco de dados
│   ├── models/           # Modelos de dados
│   ├── routes/           # Rotas da aplicação
│   │   ├── auth.py       # Autenticação
│   │   ├── alunos.py     # Gestão de alunos
│   │   ├── provas.py     # Provas diagnósticas
│   │   └── gestao.py     # Dashboard gerencial
│   ├── schemas/          # Validação de dados
│   └── static/           # Arquivos estáticos
├── templates/            # Templates HTML
│   ├── base.html         # Layout principal
│   ├── aluno/            # Área do aluno
│   └── gestor/           # Área do gestor
├── tests/                # Testes automatizados
├── .env.example          # Exemplo de variáveis de ambiente
├── alembic.ini           # Configuração do Alembic
├── main.py               # Ponto de entrada
└── requirements.txt      # Dependências do projeto

## 📄 Licença
Este projeto é de uso acadêmico, sem fins lucrativos.

## ✉️ Equipe de Desenvolvimento
Desenvolvido por Weslem Rodrigues e Iasmin Azevedo, como projeto de Arquitetura de Sistemas do IFCE - Campus Boa Viagem, demonstrando a aplicação de padrões arquiteturais modernos em soluções educacionais.
