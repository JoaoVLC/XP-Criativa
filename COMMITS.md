# Guia de Commits – Trampos

Este arquivo descreve a sequência recomendada de commits para o projeto Trampos.
Cada membro do grupo pode seguir essa ordem para manter um histórico limpo e organizado.

---

## Sequência de Commits

### 1. Estrutura inicial do backend
**Arquivos:** `trampos/backend/requirements.txt`, `trampos/backend/app/__init__.py`, `trampos/backend/app/routes/__init__.py`

```
feat(backend): estrutura inicial e dependências

Cria o esqueleto do backend FastAPI com arquivos de
inicialização e lista de dependências:
FastAPI, Uvicorn, SQLAlchemy, PyMySQL, Pydantic,
python-dotenv, passlib[bcrypt].
```

---

### 2. Configuração do banco de dados
**Arquivo:** `trampos/backend/app/database.py`

```
feat(backend): configuração da conexão com MySQL

Adiciona database.py com engine SQLAlchemy, SessionLocal
e a dependência get_db() para injeção nas rotas.
Usa variável de ambiente DATABASE_URL com fallback padrão.
```

---

### 3. Modelos do banco de dados
**Arquivo:** `trampos/backend/app/models.py`

```
feat(backend): modelos Usuario, Categoria, Vaga e Candidatura

Define as tabelas do banco via SQLAlchemy ORM espelhando
o schema XPcriativa.sql:
- Usuario (id_usuario, nome, email, senha, tipo: empresa|freelancer)
- Categoria (id_categoria, nome)
- Vaga (id_vaga, titulo, descricao, data, local, pagamento, id_empresa, id_categoria)
- Candidatura (id_candidatura, id_usuario, id_vaga, status: pendente|aceito|recusado)
Inclui relacionamentos e FKs com ON DELETE CASCADE/SET NULL.
```

---

### 4. Schemas Pydantic
**Arquivo:** `trampos/backend/app/schemas.py`

```
feat(backend): schemas Pydantic para validação de dados

Adiciona schemas de entrada e saída para todas as entidades:
UsuarioCreate/Update/Out, LoginRequest, CategoriaCreate/Out,
VagaCreate/Out, CandidaturaCreate/StatusUpdate/Out.
CandidaturaOut inclui campo vaga opcional para listar
candidaturas do usuário.
```

---

### 5. Autenticação com senha criptografada
**Arquivo:** `trampos/backend/app/routes/auth.py`

```
feat(backend): endpoint de login com bcrypt

Implementa POST /login que verifica email e senha
usando passlib[bcrypt]. Retorna dados do usuário
sem expor a senha.
```

---

### 6. CRUD de usuários com senha criptografada
**Arquivo:** `trampos/backend/app/routes/users.py`

```
feat(backend): CRUD completo de usuários

Implementa:
- POST /usuarios  → cadastro com senha hasheada (bcrypt)
- GET /usuarios   → listar todos
- GET /usuarios/{id} → buscar por ID
- PUT /usuarios/{id} → atualizar (re-hasheia senha se fornecida)
- DELETE /usuarios/{id} → excluir conta
```

---

### 7. Rotas de vagas, categorias e candidaturas
**Arquivo:** `trampos/backend/app/routes/jobs.py`

```
feat(backend): rotas de vagas, categorias e candidaturas

Implementa:
- POST/GET /categorias
- POST /vagas (somente empresa)
- GET /vagas, GET /vagas/{id}
- GET /vagas/empresa/{id} (vagas por empresa)
- DELETE /vagas/{id}
- POST /candidaturas (somente freelancer, sem duplicatas)
- GET /candidaturas/usuario/{id} (candidaturas com info da vaga)
- GET /vagas/{id}/candidaturas
- PATCH /candidaturas/{id} (aceitar/recusar)
```

---

### 8. Entry point da API
**Arquivo:** `trampos/backend/app/main.py`

```
feat(backend): entrypoint FastAPI com CORS

Registra routers de auth, usuários e vagas.
Cria tabelas no banco na inicialização.
Habilita CORS para integração com o frontend.
```

---

### 9. Variáveis de ambiente
**Arquivo:** `trampos/backend/.env.example`

```
chore: adiciona .env.example para configuração local

Modelo de arquivo .env com DATABASE_URL para facilitar
a configuração do ambiente de cada desenvolvedor.
```

---

### 10. Design System CSS responsivo
**Arquivo:** `trampos/frontend/css/styles.css`

```
feat(frontend): design system CSS completo e responsivo

Implementa variáveis de design, layout responsivo (mobile-first),
nav com hamburger, cards, formulários com estados de validação
(input-error/input-ok), badges, toasts, modal de confirmação,
skeletons de loading e media queries para mobile.
```

---

### 11. Utilitários de autenticação compartilhados
**Arquivo:** `trampos/frontend/js/auth.js`

```
feat(frontend): módulo de autenticação compartilhado

Implementa:
- getUser/setUser/logout (localStorage)
- requireLogin / requireTipo (guards de rota)
- renderNav (nav dinâmico baseado no usuário)
- showToast (notificações)
- showModal / closeModal (confirmações)
- validate / setFieldState / clearValidation (formulários)
- formatDate / formatMoney / toggleSenha (helpers)
```

---

### 12. Páginas de autenticação
**Arquivos:** `trampos/frontend/login.html`, `trampos/frontend/register.html`

```
feat(frontend): páginas de login e cadastro

login.html: formulário com validação de email e senha,
POST /login, armazenamento em localStorage.

register.html: formulário com seletor visual de tipo
(freelancer/empresa), validação de todos os campos com
RegEx, confirmação de senha e POST /usuarios.
```

---

### 13. Perfil do usuário (CRUD)
**Arquivo:** `trampos/frontend/profile.html`

```
feat(frontend): página de perfil com CRUD do usuário

Exibe dados do usuário com avatar e badge de tipo.
Permite editar nome, email e senha (PUT /usuarios/{id}).
Permite excluir a conta com confirmação (DELETE /usuarios/{id}).
Empresas veem suas vagas com opção de excluir.
Freelancers veem suas candidaturas com status colorido.
```

---

### 14. Listagem de vagas com busca e filtro
**Arquivo:** `trampos/frontend/index.html`

```
feat(frontend): listagem de vagas com busca em tempo real

Exibe vagas consumindo GET /vagas via fetch().
Filtro por texto (título, local, descrição) e por categoria.
Cards com badge de categoria, metadados e skeleton de loading.
```

---

### 15. Detalhes da vaga com gestão de candidaturas
**Arquivo:** `trampos/frontend/job.html`

```
feat(frontend): página de detalhes com gestão de candidaturas

Freelancer: vê detalhes completos e botão de candidatura (POST /candidaturas).
Empresa dona da vaga: vê lista de candidatos com botões
aceitar/recusar (PATCH /candidaturas/{id}).
Skeleton de loading e tratamento de erros.
```

---

### 16. Formulário de criação de vaga com validação
**Arquivo:** `trampos/frontend/create-job.html`

```
feat(frontend): formulário de publicação de vaga com validação

Acessível somente por usuários do tipo empresa.
Validação RegEx em todos os campos (título, local, descrição,
data, pagamento). Contador de caracteres na descrição.
Carrega categorias dinamicamente de GET /categorias.
Redireciona para a vaga criada após publicação.
```

---

### 17. Documentação do projeto
**Arquivo:** `README.md`

```
docs: atualiza instruções de instalação e uso

Descreve estrutura completa do projeto, como configurar o banco,
rodar o backend e frontend, e tabela completa de rotas da API.
```

---

## Dicas

- Cada pessoa pode pegar um ou mais commits acima para trabalhar.
- Faça commits em branches separadas (`git checkout -b feature/nome`) e abra um Pull Request.
- Não misture mudanças de backend e frontend no mesmo commit se possível.
- Use `git add -p` para fazer commits parciais de arquivos grandes.

## RNFs atendidos

| RNF | Implementação |
|-----|--------------|
| RNF 1 – Interface responsiva | CSS mobile-first, nav hamburger, grid flexível, auth pages |
| RNF 2 – Validação com RegEx | `auth.js` define `regex.*`; todos os formulários validam antes de submeter |
| RNF 3 – Persistência em BD relacional | MySQL + SQLAlchemy ORM, schema fiel ao `XPcriativa.sql` |
| RNF 4 – Autenticação com senha criptografada | `passlib[bcrypt]` no cadastro e login; CRUD completo via `profile.html` |


Este arquivo descreve a sequência recomendada de commits para o projeto Trampos.
Cada membro do grupo pode seguir essa ordem para manter um histórico limpo e organizado.

---

## Sequência de Commits

### 1. Estrutura inicial do backend
**Arquivos:** `trampos/backend/requirements.txt`, `trampos/backend/app/__init__.py`, `trampos/backend/app/routes/__init__.py`

```
feat(backend): estrutura inicial e dependências

Cria o esqueleto do backend FastAPI com os arquivos
de inicialização e lista de dependências (FastAPI,
SQLAlchemy, PyMySQL, Pydantic, python-dotenv).
```

---

### 2. Configuração do banco de dados
**Arquivo:** `trampos/backend/app/database.py`

```
feat(backend): configuração da conexão com MySQL

Adiciona database.py com engine SQLAlchemy, SessionLocal
e a dependência get_db() para injeção nas rotas.
Usa variável de ambiente DATABASE_URL com fallback padrão.
```

---

### 3. Modelos do banco de dados
**Arquivo:** `trampos/backend/app/models.py`

```
feat(backend): modelos Usuario, Categoria, Vaga e Candidatura

Define as tabelas do banco via SQLAlchemy ORM espelhando
o schema XPcriativa.sql:
- Usuario (id_usuario, nome, email, senha, tipo: empresa|freelancer)
- Categoria (id_categoria, nome)
- Vaga (id_vaga, titulo, descricao, data, local, pagamento, id_empresa, id_categoria)
- Candidatura (id_candidatura, id_usuario, id_vaga, status: pendente|aceito|recusado)
Inclui relacionamentos e FKs com ON DELETE CASCADE/SET NULL.
```

---

### 4. Schemas Pydantic
**Arquivo:** `trampos/backend/app/schemas.py`

```
feat(backend): schemas Pydantic para validação de dados

Adiciona UsuarioCreate/Out, CategoriaCreate/Out,
VagaCreate/Out e CandidaturaCreate/Out para validação
de entrada e serialização das respostas da API.
```

---

### 5. Rotas de usuários
**Arquivo:** `trampos/backend/app/routes/users.py`

```
feat(backend): rotas CRUD de usuários

Implementa POST /usuarios, GET /usuarios e GET /usuarios/{id}.
Valida email duplicado e retorna erros em português.
```

---

### 6. Rotas de vagas, categorias e candidaturas
**Arquivo:** `trampos/backend/app/routes/jobs.py`

```
feat(backend): rotas de vagas, categorias e candidaturas

Implementa:
- POST/GET /categorias
- POST /vagas (somente tipo empresa)
- GET /vagas e GET /vagas/{id_vaga}
- POST /candidaturas (somente tipo freelancer, sem duplicatas)
- GET /vagas/{id_vaga}/candidaturas
```

---

### 7. Entry point da API
**Arquivo:** `trampos/backend/app/main.py`

```
feat(backend): entrypoint FastAPI com CORS

Configura o app FastAPI, cria as tabelas no banco
na inicialização e habilita CORS para integração
com o frontend local.
```

---

### 8. Variáveis de ambiente
**Arquivo:** `trampos/backend/.env.example`

```
chore: adiciona .env.example para configuração local

Modelo de arquivo .env com a variável DATABASE_URL
para facilitar a configuração do ambiente de cada dev.
```

---

### 9. Estilos do frontend
**Arquivo:** `trampos/frontend/css/styles.css`

```
feat(frontend): estilos CSS responsivos

Adiciona layout responsivo com nav, cards de vaga,
formulários, botões, avatares e alertas.
CSS puro sem dependência de frameworks externos.
```

---

### 10. Página de listagem de vagas
**Arquivo:** `trampos/frontend/index.html`

```
feat(frontend): página inicial com lista de vagas

Exibe todas as vagas consumindo GET /vagas via fetch().
Mostra título, local, data, pagamento, empresa e categoria.
Cada card tem link para a página de detalhes.
```

---

### 11. Página de detalhes da vaga
**Arquivo:** `trampos/frontend/job.html`

```
feat(frontend): página de detalhes e candidatura

Mostra detalhes completos de uma vaga (GET /vagas/{id}),
botão de candidatura (POST /candidaturas) e lista de candidatos
com status (pendente/aceito/recusado) em tempo real.
```

---

### 12. Página de criação de vaga
**Arquivo:** `trampos/frontend/create-job.html`

```
feat(frontend): formulário para publicar vaga

Formulário para empresas criarem vagas via POST /vagas.
Inclui campo de pagamento e seleção de categoria
(carregada dinamicamente de GET /categorias).
```

---

### 13. Documentação do projeto
**Arquivo:** `README.md`

```
docs: instruções de instalação e uso do Trampos

Descreve a estrutura do projeto, como configurar o banco
de dados, rodar o backend e o frontend, e a tabela
completa de rotas da API.
```

---

## Dicas

- Cada pessoa pode pegar um ou mais commits acima para trabalhar.
- Faça commits em branches separadas (`git checkout -b feature/nome`) e abra um Pull Request.
- Não misture mudanças de backend e frontend no mesmo commit se possível.
- Use `git add -p` para fazer commits parciais de arquivos grandes.
