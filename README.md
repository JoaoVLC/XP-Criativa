# XP-Criativa

Projeto academico da disciplina Experiencia Criativa.

## Trampos

Plataforma web para conectar empresas que publicam vagas temporarias e freelancers que se candidatam com perfil, CPF e curriculo.

## Stack

- Backend: Python, FastAPI e Jinja2
- Banco de dados: MySQL
- Sessao: Starlette SessionMiddleware
- Dados: PyMySQL com SQL direto
- Seguranca de senha: bcrypt
- Interface: HTML server-side, CSS responsivo e JavaScript leve

## Como rodar

```bash
cd trampos/backend
pip install -r requirements.txt
```

Crie um arquivo `.env` com a conexao MySQL:

```bash
DATABASE_URL=mysql+pymysql://root:root@localhost/trampos
SESSION_SECRET=troque-este-segredo
```

Recrie o banco:

```bash
python seed.py
```

Execute o servidor:

```bash
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000`.

## Contas de exemplo

Todas usam a senha `senha123`.

- Administrador: `admin@trampos.dev`
- Empresa: `tech@trampos.dev`
- Freelancer: `ana@trampos.dev`

## Funcionalidades

- Cadastro separado para pessoa fisica CPF e empresa CNPJ.
- CPF/CNPJ aceitam qualquer sequencia numerica, mas nao duplicam.
- Senhas armazenadas com bcrypt.
- Upload e visualizacao de avatar.
- Curriculo PDF obrigatorio para freelancers.
- Vagas com criar, listar, editar e excluir.
- Candidaturas com criar, listar, atualizar status, cancelar e excluir.
- Empresas visualizam candidatos, historico e curriculo.
- Administrador gerencia usuarios, empresas, vagas e candidaturas.
- Notificacoes internas para eventos principais.
- Expiracao de sessao com redirecionamento para login.
- Tema claro/escuro com persistencia local.
- Filtros por area, empresa, localizacao e status.
