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
