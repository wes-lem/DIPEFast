# Guia de Comandos: Nginx + Docker (FastAPI)

## 🐧 Comandos do Nginx

### Editar Configuração

Sempre que você editar o arquivo:

```bash
sudo nano /etc/nginx/sites-available/dipefast-app
```

### Testar Configuração

Verificar se a sua mudança quebrou algo (**TESTAR**):

> **⚠️ IMPORTANTE:** Sempre rode isso antes de recarregar!

```bash
sudo nginx -t
```

### Recarregar Nginx

Aplicar suas mudanças (**RECARREGAR**):

> **ℹ️ INFO:** Isso aplica as mudanças sem derrubar ninguém que esteja usando o site.

```bash
sudo systemctl reload nginx
```

### Reiniciar Nginx

Reiniciar (se o reload falhar ou tudo travar):

```bash
sudo systemctl restart nginx
```

### Verificar Status

Ver o status do serviço do Nginx:

```bash
sudo systemctl status nginx
```

### Ver Logs de Erro

Ver logs de **ERRO** do Nginx (se aparecer 502 Bad Gateway):

```bash
sudo tail -f /var/log/nginx/error.log
```

---

## 🐳 Comandos do Docker Compose

> **⚠️ IMPORTANTE:** Sempre rode estes comandos de dentro da pasta do seu projeto:
> ```bash
> cd /home/dipe/DIPEFast
> ```

### Subir ou Recriar Containers

Subir ou recriar seus containers (**APÓS MUDAR O CÓDIGO**):

```bash
sudo docker compose up -d --build
```

**Explicação dos parâmetros:**
- `up`: Garante que está no ar
- `-d`: Roda em background
- `--build`: Força o Docker a "re-cozinhar" sua aplicação com o código novo

### Ver Logs da Aplicação

Ver os logs da sua aplicação (**VER ERROS DO PYTHON**):

> **ℹ️ INFO:** `-f` segue os logs em tempo real. `app` é o nome do seu serviço no `docker-compose.yml`.

```bash
sudo docker compose logs -f app
```

### Ver Logs de Todos os Serviços

Ver os logs de **TUDO** (App + Banco de Dados):

```bash
sudo docker compose logs -f
```

### Listar Containers

Ver quais containers estão rodando:

```bash
docker ps
```

Ou apenas os containers deste projeto:

```bash
sudo docker compose ps
```

### Parar Todos os Serviços

Parar **TUDO** (App + Banco de Dados):

> **ℹ️ INFO:** Use isso se quiser parar completamente os serviços.

```bash
sudo docker compose down
```

---

## 🛠️ Cenários Comuns: O "Como eu faço para..."

### 1. Mudar código Python ou adicionar biblioteca

**"...mudar meu código Python (ex: `main.py`) ou adicionar uma biblioteca (ex: `requirements.txt`)?"**

1. Faça suas alterações no código
2. Vá para a pasta:
   ```bash
   cd /home/dipe/DIPEFast
   ```
3. Rode o comando mágico:
   ```bash
   sudo docker compose up -d --build
   ```
4. Verifique os logs para ter certeza que subiu bem:
   ```bash
   sudo docker compose logs -f app
   ```

---

### 2. Mudar arquivos estáticos

**"...mudar SÓ um arquivo CSS, JS ou uma imagem?"**

1. Substitua o arquivo na pasta `/home/dipe/DIPEFast/templates/static`
2. **Não faça NADA** (nem Nginx, nem Docker)
3. Vá no seu navegador e dê um **"Hard Refresh"** (Limpar Cache):
   - **Windows/Linux:** `Ctrl+Shift+R`
   - **Mac:** `Cmd+Shift+R`

> **ℹ️ INFO:** Isso funciona porque o Nginx está servindo os arquivos direto do seu disco!

---

### 3. Mudar porta do Nginx

**"...mudar a porta que o Nginx usa (ex: de 8080 para 8081)?"**

1. Edite o arquivo:
   ```bash
   sudo nano /etc/nginx/sites-available/dipefast-app
   ```
2. Mude o `listen 8080;` para `listen 8081;`
3. Teste:
   ```bash
   sudo nginx -t
   ```
4. Recarregue:
   ```bash
   sudo systemctl reload nginx
   ```

> **⚠️ ATENÇÃO:** Você terá que abrir a nova porta (8081) no `ufw` **E** pedir ao TI para liberar no firewall externo.

---

### 4. Reiniciar após reboot do servidor

**"...reiniciar tudo depois que o servidor da faculdade foi reiniciado?"**

Graças à sua configuração `restart: unless-stopped` (no Docker) e `systemctl enable` (no Nginx), você não precisa fazer nada. Tudo deve subir sozinho.

**Se por acaso não subir:**

1. Vá para a pasta:
   ```bash
   cd /home/dipe/DIPEFast
   ```
2. Suba os containers:
   ```bash
   sudo docker compose up -d
   ```
3. Verifique o Nginx:
   ```bash
   sudo systemctl status nginx
   ```
   Se não estiver `active`, rode:
   ```bash
   sudo systemctl start nginx
   ```
