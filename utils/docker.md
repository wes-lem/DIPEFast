# Comandos Úteis Docker
- Para rodar em segundo plano (recomendado):
```bash
docker compose up -d 
```
(O -d significa "detached". Isso libera seu terminal).

Para ver os logs da sua aplicação:

```bash
docker compose logs -f app
```
(O -f segue os logs em tempo real. Use Ctrl+C para sair).

Para parar tudo:
```bash
docker compose down
```
(Isso para e remove os containers, mas não apaga os dados do seu banco, pois eles estão no volume db_data).

# Em desevolvimento:
- Comentar o static e deixar o .app exposto
```bash
volumes:
      - .:/app  # Mapeia toda a raiz do projeto para /app no container
    # - /home/dipe/DIPEFast/templates/static:/app/templates/static
```
Para reiniciar os containers:
```bash
docker compose restart

ou

docker compose down
docker compose up -d 
```

Para voltar para produção comente a linha 
```bash
volumes:
    # - .:/app  # Mapeia toda a raiz do projeto para /app no container
    - /home/dipe/DIPEFast/templates/static:/app/templates/static
```
Para reiniciar os containers:
```bash
docker compose up -d --build
```

# Problemas Comuns

## Erro "MySQL server has gone away"

Este erro ocorre quando a conexão com o MySQL expira ou é perdida. A aplicação já está configurada para lidar com isso através de:

- **pool_pre_ping=True**: Verifica se a conexão está viva antes de usar
- **pool_recycle=3600**: Recicla conexões após 1 hora
- **pool_size=10**: Mantém um pool de 10 conexões
- **max_overflow=20**: Permite até 20 conexões adicionais

Se o erro persistir, tente reiniciar os containers:
```bash
docker compose restart
```
