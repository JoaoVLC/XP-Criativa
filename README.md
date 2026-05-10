# XP-Criativa
Projeto da disciplina Experiência Criativa

---

## Trampos

Plataforma simples para conectar pequenos negócios que precisam de trabalhadores temporários com pessoas em busca de bicos rápidos.

### Stack
- **Backend:** Python + FastAPI + Jinja
- **Banco de dados:** MySQL
- **Sessão e formulários:** SessionMiddleware + POST/Redirect/GET
- **Acesso a dados:** PyMySQL com SQL direto

---

### Estrutura

```
trampos/
├── backend/
│   ├── app/
│   │   ├── main.py          # Entrypoint FastAPI
│   │   └── database.py      # Conexão com MySQL sem ORM
│   ├── static/
│   │   └── css/styles.css   # Estilos servidos pelo FastAPI
│   ├── templates/           # Templates Jinja server-side
│   ├── requirements.txt
│   ├── seed.py              # Recria e popula o banco a partir do SQL
│   └── trampos.sql
└── frontend/                # Protótipos originais mantidos no repositório
```

---

### Como rodar

#### 1. Banco de dados

O backend usa a variável `DATABASE_URL`. Exemplo:

```bash
DATABASE_URL=mysql+pymysql://root:123456@localhost/trampos
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

# Configure o banco no arquivo .env
# Exemplo:
# DATABASE_URL=mysql+pymysql://root:123456@localhost/trampos

# Crie e popule o banco
python seed.py

# Rode o servidor
uvicorn app.main:app --reload
```

O servidor sobe em **http://localhost:8000**
Documentação automática em **http://localhost:8000/docs**

---

### Fluxo de uso

1. **Acesse `/`** para listar vagas com filtro por texto e categoria.
2. **Cadastre-se** como empresa ou freelancer.
3. **Empresas** publicam vagas e acompanham candidatos.
4. **Freelancers** se candidatam e acompanham o status pelo perfil.

---

### Rotas principais

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Listagem de vagas |
| GET/POST | `/login` | Login por formulário |
| GET/POST | `/cadastro` | Cadastro de usuário |
| GET | `/logout` | Encerrar sessão |
| GET/POST | `/vaga/nova` | Publicar vaga |
| GET | `/vaga/{id_vaga}` | Detalhe da vaga |
| POST | `/vaga/{id_vaga}/candidatar` | Enviar candidatura |
| POST | `/candidaturas/{id_candidatura}/status` | Aceitar ou recusar candidatura |
| GET/POST | `/perfil` | Visualizar e editar perfil |
| POST | `/perfil/excluir` | Excluir conta |
