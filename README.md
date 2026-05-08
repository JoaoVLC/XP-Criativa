# XP-Criativa
Projeto da disciplina Experiência Criativa

---

## Trampos

Plataforma simples para conectar pequenos negócios que precisam de trabalhadores temporários com pessoas em busca de bicos rápidos.

### Stack
- **Backend:** Python + FastAPI + PyMySQL
- **Banco de dados:** MySQL
- **Frontend:** HTML + CSS + JavaScript puro

---

### Estrutura

```
trampos/
├── backend/
│   ├── app/
│   │   ├── main.py          # Entrypoint FastAPI
│   │   ├── database.py      # Conexão com MySQL
│   │   ├── models.py        # Arquivo de modelos legado
│   │   ├── schemas.py       # Schemas Pydantic
│   │   └── routes/
│   │       ├── jobs.py      # Rotas de vagas e candidaturas
│   │       └── users.py     # Rotas de usuários
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html       # Lista de vagas
    ├── job.html         # Detalhes da vaga + candidatura
    ├── create-job.html  # Formulário para criar vaga
    └── css/
        └── styles.css
```

---

### Como rodar

#### 1. Banco de dados

Crie o banco no MySQL:
```sql
CREATE DATABASE trampos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. Backend

```bash
cd trampos/backend

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco (copie e edite o .env)
cp .env.example .env
# Edite DATABASE_URL em .env se necessário

# Rode o servidor
uvicorn app.main:app --reload
```

O servidor sobe em **http://localhost:8000**
Documentação automática em **http://localhost:8000/docs**

#### 3. Frontend

Abra o arquivo `trampos/frontend/index.html` no navegador — ou sirva com:

```bash
cd trampos/frontend
python -m http.server 3000
# Acesse http://localhost:3000
```

---

### Fluxo de uso

1. **Crie usuários** via `POST /users` (ou pela interface `/docs`):
   - Um `employer` (empregador) e um `worker` (trabalhador)
2. **Empregador cria vagas** em `create-job.html` usando seu ID
3. **Trabalhador vê vagas** em `index.html` e se candidata em `job.html`
4. A vaga mostra a lista de candidatos em tempo real

---

### Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/users` | Criar usuário |
| GET | `/users` | Listar usuários |
| GET | `/users/{id}` | Buscar usuário |
| POST | `/jobs` | Criar vaga |
| GET | `/jobs` | Listar vagas |
| GET | `/jobs/{id}` | Detalhe da vaga |
| POST | `/apply` | Candidatar-se a uma vaga |
| GET | `/jobs/{id}/applications` | Ver candidatos da vaga |
