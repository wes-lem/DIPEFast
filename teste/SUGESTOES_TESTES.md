# Sugestões de Testes para Implementar

Este documento lista sugestões adicionais de testes que podem ser implementados no sistema DIPEFast.

## ✅ Testes Já Implementados

1. **Testes de Rotas** (`test_routes.py`)
   - Rotas públicas
   - Rotas protegidas (verificação de autenticação)
   - Prevenção de erros 500

2. **Testes de Login** (`test_login.py`)
   - Validação de credenciais
   - Campos obrigatórios

3. **Testes de Modelos** (`test_models.py`)
   - Criação de entidades
   - Validação de campos

4. **Testes de DAOs** (`test_daos.py`)
   - Operações CRUD
   - Filtros e buscas

5. **Testes de Lógica de Negócio** (`test_business_logic.py`)
   - Filtragem de formulários
   - Questões públicas vs privadas

## 📋 Testes Sugeridos para Implementar

### 1. Testes de Validação de Dados
**Arquivo:** `teste/test_validation.py`

```python
- Validar formato de email
- Validar força de senha
- Validar tamanho máximo de campos
- Validar campos obrigatórios
- Validar tipos de dados (int, str, etc)
- Validar valores de enum (status, tipo, etc)
- Validar formato de datas
- Validar upload de arquivos (tipo, tamanho)
```

### 2. Testes de Integração Completa
**Arquivo:** `teste/test_integration.py`

```python
- Fluxo completo: Cadastro → Login → Dashboard
- Fluxo completo: Criar Questão → Criar Prova → Disponibilizar
- Fluxo completo: Criar Formulário → Aluno Responde → Ver Respostas
- Fluxo completo: Criar Turma → Adicionar Alunos → Aplicar Prova
- Testar múltiplos usuários simultâneos
- Testar transações complexas
```

### 3. Testes de Permissões e Autorização
**Arquivo:** `teste/test_permissions.py`

```python
- Aluno não pode acessar rotas de professor
- Professor não pode acessar rotas de gestor
- Aluno não pode ver dados de outros alunos
- Professor não pode editar questões de outros professores
- Gestor pode acessar todas as rotas
- Verificar acesso a recursos por ID (prevenir acesso não autorizado)
```

### 4. Testes de Upload de Arquivos
**Arquivo:** `teste/test_file_upload.py`

```python
- Upload de imagem válida
- Upload de arquivo inválido (não é imagem)
- Upload de arquivo muito grande
- Upload de múltiplos formatos (jpg, png, etc)
- Verificar salvamento no caminho correto
- Verificar remoção de arquivo antigo ao atualizar
- Testar crop de imagem (1x1)
```

### 5. Testes de Cálculos e Estatísticas
**Arquivo:** `teste/test_calculations.py`

```python
- Cálculo de notas de provas
- Cálculo de médias
- Cálculo de estatísticas de desempenho
- Geração de gráficos (verificar dados)
- Cálculos de relatórios
- Percentuais e proporções
```

### 6. Testes de Notificações
**Arquivo:** `teste/test_notifications.py`

```python
- Criação de notificações
- Filtragem de notificações por aluno
- Marcação como lida
- Remoção de notificações
- Notificações de formulários direcionados
- Validação de notificações (formulário existe)
- Limpeza de notificações órfãs
```

### 7. Testes de Relatórios e Exportação
**Arquivo:** `teste/test_reports.py`

```python
- Geração de relatório PDF
- Geração de relatório DOCX
- Exportação de dados
- Formatação de relatórios
- Dados corretos nos relatórios
- Performance de geração de relatórios grandes
```

### 8. Testes de Segurança
**Arquivo:** `teste/test_security.py`

```python
- SQL Injection (tentar injeção em campos de busca)
- XSS (Cross-Site Scripting) em campos de texto
- Validação de hash de senhas (não armazenar em texto plano)
- Expiração de sessões
- Proteção CSRF (se implementado)
- Validação de cookies
- Rate limiting (se implementado)
```

### 9. Testes de Performance
**Arquivo:** `teste/test_performance.py`

```python
- Tempo de resposta de rotas principais (< 1s)
- Carga de múltiplas requisições simultâneas
- Consultas ao banco de dados (otimização)
- Carregamento de listas grandes
- Geração de relatórios complexos
```

### 10. Testes de API (Endpoints JSON)
**Arquivo:** `teste/test_api.py`

```python
- Estrutura de respostas JSON
- Códigos de status HTTP corretos
- Serialização/deserialização
- Validação de schemas
- Tratamento de erros em JSON
```

### 11. Testes de Turmas
**Arquivo:** `teste/test_turmas.py`

```python
- Criação de turma
- Geração de código único de turma
- Adicionar aluno à turma
- Remover aluno da turma
- Listar alunos de uma turma
- Arquivar turma
```

### 12. Testes de Provas
**Arquivo:** `teste/test_provas.py`

```python
- Criar prova com questões
- Disponibilizar prova para turma
- Aluno responder prova
- Calcular nota automaticamente
- Verificar expiração de provas
- Listar provas disponíveis
```

### 13. Testes de Formulários
**Arquivo:** `teste/test_formularios.py`

```python
- Criar formulário com perguntas
- Aluno responder formulário
- Verificar se aluno já respondeu
- Filtrar formulários por turma/campus/curso
- Listar respostas de formulário
- Exportar respostas
```

### 14. Testes de Questões
**Arquivo:** `teste/test_questoes.py`

```python
- Criar questão pública
- Criar questão privada
- Editar questão
- Arquivar questão
- Buscar questões públicas
- Adicionar questão à prova
- Remover questão de prova
```

### 15. Testes de Validação de Formulários HTML
**Arquivo:** `teste/test_forms.py`

```python
- Validação de campos obrigatórios no frontend
- Validação de tipos de dados
- Validação de tamanhos máximos
- Prevenção de submissão duplicada
- Validação de seleção de questões
```

### 16. Testes de Banco de Dados
**Arquivo:** `teste/test_database.py`

```python
- Migrações de banco
- Constraints (foreign keys, unique)
- Índices
- Transações
- Rollback em caso de erro
- Integridade referencial
```

### 17. Testes de Serviços
**Arquivo:** `teste/test_services.py`

```python
- Geração de gráficos (verificar dados)
- Cálculo de estatísticas
- Processamento de dados
- Transformação de dados
```

### 18. Testes de Utilitários
**Arquivo:** `teste/test_utils.py`

```python
- Criptografia de senhas
- Hash de senhas
- Validação de tokens (se houver)
- Formatação de dados
- Conversão de tipos
```

## 🎯 Prioridade de Implementação

### Alta Prioridade (Implementar Primeiro)
1. ✅ Testes de Rotas (JÁ IMPLEMENTADO)
2. ✅ Testes de Login (JÁ IMPLEMENTADO)
3. ⚠️ **Testes de Permissões** - Importante para segurança
4. ⚠️ **Testes de Validação** - Previne bugs
5. ⚠️ **Testes de Integração** - Garante fluxos completos

### Média Prioridade
6. Testes de Upload de Arquivos
7. Testes de Notificações
8. Testes de Cálculos
9. Testes de Formulários
10. Testes de Provas

### Baixa Prioridade (Opcional)
11. Testes de Performance
12. Testes de Segurança Avançada
13. Testes de Relatórios
14. Testes de API

## 📝 Boas Práticas para Criar Testes

1. **Nomes Descritivos**: Use nomes que descrevam claramente o que está sendo testado
2. **Um Teste = Uma Funcionalidade**: Cada teste deve verificar uma coisa específica
3. **Teste Casos de Sucesso e Erro**: Teste tanto o caminho feliz quanto os erros
4. **Isolamento**: Cada teste deve ser independente
5. **Fixtures**: Use fixtures para dados comuns (já criadas em conftest.py)
6. **Assertions Claras**: Use mensagens de erro descritivas
7. **Cobertura**: Procure cobrir pelo menos 80% do código

## 🔧 Comandos Úteis

```bash
# Executar todos os testes
pytest teste/

# Executar com verbose
pytest teste/ -v

# Executar apenas testes que falharam na última execução
pytest teste/ --lf

# Executar testes com cobertura
pytest teste/ --cov=. --cov-report=html

# Executar testes específicos
pytest teste/test_routes.py::TestRotasPublicas

# Executar testes em paralelo (mais rápido)
pip install pytest-xdist
pytest teste/ -n auto

# Executar testes com output mais detalhado
pytest teste/ -vv -s
```

## 📊 Métricas de Qualidade

- **Cobertura de Código**: Buscar 80%+
- **Taxa de Sucesso**: 100% dos testes devem passar
- **Tempo de Execução**: Todos os testes devem rodar em < 30 segundos
- **Manutenibilidade**: Testes devem ser fáceis de entender e manter

