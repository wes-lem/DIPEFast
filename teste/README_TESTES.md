# Guia de Testes - DIPEFast

Este diretório contém os testes automatizados do sistema DIPEFast usando pytest.

## Estrutura de Testes

```
teste/
├── conftest.py              # Configurações e fixtures compartilhadas
├── test_routes.py           # Testes para todas as rotas da aplicação
├── test_login.py            # Testes de autenticação e login
├── test_models.py           # Testes para modelos de dados
├── test_daos.py             # Testes para Data Access Objects
├── test_business_logic.py   # Testes para lógica de negócio
├── run_tests.py             # Script auxiliar para executar testes
├── README_TESTES.md         # Este arquivo
└── SUGESTOES_TESTES.md      # Sugestões de testes adicionais
```

## Como Executar os Testes

### ⚠️ IMPORTANTE: Ativar o Ambiente Virtual Primeiro!

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Instalar Dependências

**Opção 1: Usando o script (mais fácil)**

**Windows:**
```powershell
# PowerShell
.\teste\instalar.ps1

# CMD
teste\instalar.bat
```

**Opção 2: Manualmente**

Com o venv ativado:

```bash
pip install -r requirements.txt
```

Ou instale apenas as dependências de teste:
```bash
pip install pytest==8.3.4 pytest-asyncio==0.24.0 httpx==0.27.2 pytest-cov==6.0.0
```

### Executar Todos os Testes

```bash
pytest teste/
```

### Executar Testes Específicos

```bash
# Testar apenas rotas
pytest teste/test_routes.py

# Testar apenas login
pytest teste/test_login.py

# Testar apenas modelos
pytest teste/test_models.py

# Testar uma classe específica
pytest teste/test_routes.py::TestRotasPublicas

# Testar um teste específico
pytest teste/test_routes.py::TestRotasPublicas::test_rota_home
```

### Executar com Verbose

```bash
pytest teste/ -v
```

### Executar com Cobertura

```bash
pip install pytest-cov
pytest teste/ --cov=. --cov-report=html
```

## Tipos de Testes Implementados

### 1. Testes de Rotas (`test_routes.py`)
- ✅ Testa todas as rotas públicas
- ✅ Testa rotas protegidas (verifica se requerem autenticação)
- ✅ Verifica se rotas não retornam erro 500 (Internal Server Error)
- ✅ Testa rotas inválidas

### 2. Testes de Login (`test_login.py`)
- ✅ Testa login com credenciais inválidas
- ✅ Testa validação de campos obrigatórios
- ✅ Testa login com credenciais válidas
- ✅ Testa logout

### 3. Testes de Modelos (`test_models.py`)
- ✅ Testa criação de usuários
- ✅ Testa criação de alunos
- ✅ Testa criação de formulários
- ✅ Testa criação de questões públicas/privadas

## Testes Sugeridos para Implementar

### 4. Testes de DAOs (Data Access Objects)
```python
# teste/test_daos.py
- Testar criação de registros
- Testar busca de registros
- Testar atualização de registros
- Testar deleção de registros
- Testar relacionamentos entre modelos
```

### 5. Testes de Validação de Dados
```python
# teste/test_validation.py
- Testar validação de emails
- Testar validação de senhas
- Testar validação de campos obrigatórios
- Testar validação de tipos de dados
- Testar limites de campos (tamanho máximo, etc)
```

### 6. Testes de Lógica de Negócio
```python
# teste/test_business_logic.py
- Testar cálculo de notas
- Testar filtragem de formulários por turma/campus/curso
- Testar busca de questões públicas vs privadas
- Testar geração de relatórios
- Testar criação de notificações
```

### 7. Testes de Integração
```python
# teste/test_integration.py
- Testar fluxo completo de cadastro de aluno
- Testar fluxo completo de criação de prova
- Testar fluxo completo de resposta de formulário
- Testar integração entre componentes
```

### 8. Testes de Upload de Arquivos
```python
# teste/test_file_upload.py
- Testar upload de imagens
- Testar validação de tipos de arquivo
- Testar tamanho máximo de arquivos
- Testar salvamento de arquivos
```

### 9. Testes de Permissões e Autorização
```python
# teste/test_permissions.py
- Testar acesso de aluno a rotas de professor
- Testar acesso de professor a rotas de gestor
- Testar acesso não autenticado a rotas protegidas
- Testar acesso a recursos de outros usuários
```

### 10. Testes de Performance
```python
# teste/test_performance.py
- Testar tempo de resposta de rotas principais
- Testar carga de múltiplas requisições
- Testar consultas ao banco de dados
```

### 11. Testes de Segurança
```python
# teste/test_security.py
- Testar SQL injection
- Testar XSS (Cross-Site Scripting)
- Testar CSRF (Cross-Site Request Forgery)
- Testar validação de sessões
- Testar hash de senhas
```

### 12. Testes de API (se houver endpoints JSON)
```python
# teste/test_api.py
- Testar endpoints JSON
- Testar serialização/deserialização
- Testar códigos de status HTTP corretos
- Testar estrutura de respostas
```

### 13. Testes de Notificações
```python
# teste/test_notifications.py
- Testar criação de notificações
- Testar filtragem de notificações por aluno
- Testar marcação como lida
- Testar notificações de formulários direcionados
```

### 14. Testes de Relatórios
```python
# teste/test_reports.py
- Testar geração de relatórios
- Testar exportação PDF/DOCX
- Testar cálculos de estatísticas
- Testar gráficos
```

## Fixtures Disponíveis

As fixtures estão definidas em `conftest.py`:

- `db_session`: Sessão de banco de dados de teste (SQLite em memória)
- `client`: Cliente de teste FastAPI
- `usuario_aluno`: Usuário do tipo aluno
- `usuario_professor`: Usuário do tipo professor
- `usuario_gestor`: Usuário do tipo gestor
- `aluno_completo`: Aluno completo com todos os dados
- `campus_teste`: Campus de teste
- `professor_completo`: Professor completo
- `gestor_completo`: Gestor completo
- `client_com_auth`: Cliente autenticado como aluno
- `client_com_auth_professor`: Cliente autenticado como professor
- `client_com_auth_gestor`: Cliente autenticado como gestor

## Configuração do Ambiente de Teste

Os testes usam um banco de dados SQLite em memória, isolado para cada teste. Isso garante:
- Testes independentes
- Execução rápida
- Não interfere com banco de dados de desenvolvimento

## Boas Práticas

1. **Um teste por funcionalidade**: Cada teste deve verificar uma coisa específica
2. **Nomes descritivos**: Nomes de testes devem descrever o que está sendo testado
3. **Isolamento**: Cada teste deve ser independente e poder rodar sozinho
4. **Limpeza**: Fixtures garantem limpeza automática após cada teste
5. **Assertions claras**: Use mensagens de erro claras quando possível

## Executar Testes Continuamente

Para desenvolvimento, você pode usar:

```bash
# Executar testes continuamente com watch
pip install pytest-watch
ptw teste/
```

## Integração Contínua (CI)

Para adicionar testes em CI/CD, adicione ao seu `.github/workflows/test.yml` ou similar:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest teste/ -v
```

## Notas Importantes

- Os testes usam um banco de dados SQLite em memória, então algumas funcionalidades específicas do MySQL podem não funcionar
- Testes de autenticação podem precisar de ajustes dependendo da implementação de sessões
- Para testar rotas que usam templates, os testes verificam principalmente códigos de status HTTP

