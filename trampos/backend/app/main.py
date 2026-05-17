from __future__ import annotations

import base64
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import bcrypt
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import SESSION_SECRET, get_connection

# Caminhos usados pelo FastAPI para encontrar os arquivos estaticos e os templates.
BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Constantes reutilizadas nas validacoes e na exibicao das candidaturas.
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
STATUS_LABELS = {
    "pendente": "⏳ Pendente",
    "aceito": "✅ Aceito",
    "recusado": "❌ Recusado",
}
STATUS_CLASSES = {
    "pendente": "warning",
    "aceito": "success",
    "recusado": "danger",
}
MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_MIMES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

# Instancia principal da aplicacao e configuracao da sessao do usuario.
app = FastAPI(title="Trampos", version="3.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="trampos_session",
    max_age=30 * 60,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Motor de templates usado para renderizar as paginas HTML.
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def static_asset_url(request: Request, path: str) -> str:
    # Adiciona a data de modificacao na URL para evitar cache antigo de CSS/imagens.
    normalized_path = path.lstrip("/")
    asset_path = STATIC_DIR / normalized_path
    asset_url = str(request.url_for("static", path=normalized_path))

    if asset_path.is_file():
        return f"{asset_url}?v={int(asset_path.stat().st_mtime)}"

    return asset_url


# Filtros e helpers de formatacao usados diretamente nos templates Jinja.
def format_date_br(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y")


def format_money_br(value: Any) -> str:
    if value in (None, ""):
        return ""
    decimal_value = Decimal(str(value))
    formatted = f"{decimal_value:,.2f}"
    return f"R$ {formatted}".replace(",", "X").replace(".", ",").replace("X", ".")


# Helpers para exibir avatar salvo no banco ou uma inicial quando nao houver imagem.
def avatar_initial(name: str | None) -> str:
    if not name:
        return "?"
    return name.strip()[0].upper()


def detect_image_mime(file_bytes: bytes) -> str | None:
    # Confere a assinatura real do arquivo, nao apenas o content-type enviado pelo navegador.
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


def avatar_data_url(avatar: bytes | None, avatar_mime: str | None) -> str | None:
    if not avatar:
        return None

    mime = avatar_mime or detect_image_mime(avatar) or "image/png"
    encoded = base64.b64encode(avatar).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def enrich_avatar(record: dict[str, Any] | None, *, avatar_key: str = "avatar", mime_key: str = "avatar_mime") -> dict[str, Any] | None:
    # Cria uma copia do registro com o avatar pronto para ser usado no atributo src do HTML.
    if not record:
        return None

    enriched = dict(record)
    enriched["avatar_data"] = avatar_data_url(enriched.get(avatar_key), enriched.get(mime_key))
    return enriched


templates.env.filters["date_br"] = format_date_br
templates.env.filters["money_br"] = format_money_br
templates.env.globals["avatar_initial"] = avatar_initial
templates.env.globals["static_asset_url"] = static_asset_url
templates.env.globals["status_label"] = lambda status_value: STATUS_LABELS.get(status_value, status_value)
templates.env.globals["status_class"] = lambda status_value: STATUS_CLASSES.get(status_value, "secondary")


# Helpers de sessao, mensagens e respostas.
def current_user(request: Request) -> dict[str, Any] | None:
    return request.session.get("user")


def flash(request: Request, message: str, kind: str = "info") -> None:
    request.session["flash"] = {"message": message, "type": kind}


def apply_response_headers(response: HTMLResponse | RedirectResponse) -> HTMLResponse | RedirectResponse:
    # Evita que paginas autenticadas fiquem reaparecendo pelo botao "voltar" apos logout.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def sync_session_user(request: Request) -> dict[str, Any] | None:
    # Recarrega o usuario do banco a cada request para manter a sessao atualizada.
    session_user = current_user(request)
    if not session_user:
        return None

    db_user = get_user_by_id(session_user["id_usuario"])
    if not db_user:
        request.session.clear()
        flash(request, "Sua sessao nao e mais valida. Faca login novamente.", "error")
        return None

    request.session["user"] = db_user
    return db_user


def require_user(request: Request, role: str | None = None) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    # Centraliza a protecao de rotas que exigem login e, opcionalmente, tipo de usuario.
    user = sync_session_user(request)
    if not user:
        if "flash" not in request.session:
            flash(request, "Faca login para continuar.", "error")
        return None, redirect_to("/login")

    if role and user["tipo"] != role:
        flash(request, "Voce nao tem permissao para acessar esta pagina.", "error")
        return None, redirect_to("/")

    return user, None


def redirect_to(url: str) -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    return apply_response_headers(response)


def render_template(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    # Monta o contexto padrao compartilhado por todas as paginas.
    user = sync_session_user(request)
    user_profile = get_user_profile(user["id_usuario"]) if user else None
    payload = {
        "request": request,
        "user": user,
        "user_avatar_data": user_profile["avatar_data"] if user_profile else None,
        "flash": request.session.pop("flash", None),
        "active_page": "",
        "page_title": "Trampos",
        "show_nav": True,
    }
    if context:
        payload.update(context)
    response = templates.TemplateResponse(
        request=request,
        name=template_name,
        context=payload,
        status_code=status_code,
    )
    return apply_response_headers(response)


# Helpers simples de normalizacao e validacao de formularios.
def normalize_text(value: str) -> str:
    return value.strip()


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


# Funcoes pequenas para executar SQL e sempre fechar a conexao.
def query_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()


def query_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        connection.close()


# Consultas de leitura usadas pelas rotas.
def get_categories() -> list[dict[str, Any]]:
    return query_all("SELECT id_categoria, nome FROM Categoria ORDER BY nome")


def get_jobs(*, search: str = "", category_id: int | None = None, company_id: int | None = None) -> list[dict[str, Any]]:
    # Monta filtros opcionais sem concatenar valores diretamente no SQL.
    sql = """
        SELECT
            V.id_vaga,
            V.titulo,
            V.descricao,
            V.data,
            V.local,
            V.pagamento,
            V.id_empresa,
            V.id_categoria,
            U.nome AS empresa_nome,
            C.nome AS categoria_nome
        FROM Vaga AS V
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
    """
    conditions: list[str] = []
    params: list[Any] = []

    if search:
        like = f"%{search}%"
        conditions.append("(V.titulo LIKE %s OR V.local LIKE %s OR V.descricao LIKE %s OR U.nome LIKE %s)")
        params.extend([like, like, like, like])

    if category_id:
        conditions.append("V.id_categoria = %s")
        params.append(category_id)

    if company_id:
        conditions.append("V.id_empresa = %s")
        params.append(company_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY V.data ASC, V.id_vaga DESC"
    return query_all(sql, tuple(params))


def get_job(id_vaga: int) -> dict[str, Any] | None:
    return query_one(
        """
        SELECT
            V.id_vaga,
            V.titulo,
            V.descricao,
            V.data,
            V.local,
            V.pagamento,
            V.id_empresa,
            V.id_categoria,
            U.nome AS empresa_nome,
            U.email AS empresa_email,
            C.nome AS categoria_nome
        FROM Vaga AS V
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
        WHERE V.id_vaga = %s
        """,
        (id_vaga,),
    )


def get_user_by_email(email: str) -> dict[str, Any] | None:
    return query_one(
        """
        SELECT id_usuario, nome, email, senha, tipo
        FROM Usuario
        WHERE email = %s
        """,
        (email,),
    )


def get_user_by_id(id_usuario: int) -> dict[str, Any] | None:
    return query_one(
        """
        SELECT id_usuario, nome, email, tipo
        FROM Usuario
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )


def get_user_profile(id_usuario: int) -> dict[str, Any] | None:
    record = query_one(
        """
        SELECT id_usuario, nome, email, tipo, avatar, avatar_mime
        FROM Usuario
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )
    return enrich_avatar(record)


def get_applications_for_job(id_vaga: int) -> list[dict[str, Any]]:
    records = query_all(
        """
        SELECT
            C.id_candidatura,
            C.id_usuario,
            C.id_vaga,
            C.status,
            U.nome AS usuario_nome,
            U.email AS usuario_email,
            U.avatar,
            U.avatar_mime
        FROM Candidatura AS C
        JOIN Usuario AS U ON U.id_usuario = C.id_usuario
        WHERE C.id_vaga = %s
        ORDER BY
            CASE C.status
                WHEN 'pendente' THEN 0
                WHEN 'aceito' THEN 1
                ELSE 2
            END,
            U.nome
        """,
        (id_vaga,),
    )
    return [enrich_avatar(record) for record in records]


def get_application_stats(id_vaga: int, id_usuario: int | None = None) -> dict[str, Any]:
    stats = query_one(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN id_usuario = %s THEN 1 ELSE 0 END) AS do_usuario
        FROM Candidatura
        WHERE id_vaga = %s
        """,
        (id_usuario or 0, id_vaga),
    )
    return stats or {"total": 0, "do_usuario": 0}


def get_company_jobs(id_empresa: int) -> list[dict[str, Any]]:
    return query_all(
        """
        SELECT
            V.id_vaga,
            V.titulo,
            V.local,
            V.data,
            V.pagamento,
            C.nome AS categoria_nome,
            COUNT(A.id_candidatura) AS total_candidaturas
        FROM Vaga AS V
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
        LEFT JOIN Candidatura AS A ON A.id_vaga = V.id_vaga
        WHERE V.id_empresa = %s
        GROUP BY V.id_vaga, V.titulo, V.local, V.data, V.pagamento, C.nome
        ORDER BY V.data ASC, V.id_vaga DESC
        """,
        (id_empresa,),
    )


def get_user_applications(id_usuario: int) -> list[dict[str, Any]]:
    return query_all(
        """
        SELECT
            C.id_candidatura,
            C.status,
            C.id_vaga,
            V.titulo,
            V.local,
            V.data,
            V.pagamento,
            U.nome AS empresa_nome,
            C2.nome AS categoria_nome
        FROM Candidatura AS C
        JOIN Vaga AS V ON V.id_vaga = C.id_vaga
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C2 ON C2.id_categoria = V.id_categoria
        WHERE C.id_usuario = %s
        ORDER BY V.data ASC, C.id_candidatura DESC
        """,
        (id_usuario,),
    )


def build_profile_context(user: dict[str, Any], form_data: dict[str, Any] | None = None, errors: dict[str, str] | None = None) -> dict[str, Any]:
    # O perfil mostra informacoes diferentes para empresa e freelancer.
    profile_user = get_user_profile(user["id_usuario"]) or dict(user)
    profile_form = form_data or {
        "nome": profile_user["nome"],
        "email": profile_user["email"],
    }
    context = {
        "active_page": "perfil",
        "page_title": "Meu Perfil",
        "form_data": profile_form,
        "errors": errors or {},
        "profile_user": profile_user,
    }

    if user["tipo"] == "empresa":
        context["jobs"] = get_company_jobs(user["id_usuario"])
        context["applications"] = []
    else:
        context["jobs"] = []
        context["applications"] = get_user_applications(user["id_usuario"])

    return context


# Conversores usados para tratar valores recebidos dos formularios e da URL.
def parse_category(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_future_date(value: str) -> date | None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    return parsed


# Rotas publicas de listagem, login, cadastro e logout.
@app.get("/", response_class=HTMLResponse)
def home(request: Request, busca: str = "", categoria: str = ""):
    sync_session_user(request)
    categoria_id = parse_category(categoria)
    categories = get_categories()
    jobs = get_jobs(search=normalize_text(busca), category_id=categoria_id)

    return render_template(
        request,
        "index.html",
        {
            "page_title": "Vagas Disponíveis",
            "active_page": "vagas",
            "categorias": categories,
            "vagas": jobs,
            "filtros": {"busca": busca, "categoria": categoria},
        },
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if sync_session_user(request):
        return redirect_to("/")
    return render_template(
        request,
        "login.html",
        {
            "page_title": "Entrar",
            "show_nav": False,
            "body_class": "auth-page",
            "errors": {},
            "form_data": {"email": ""},
        },
    )


@app.post("/login")
def login(request: Request, email: str = Form(...), senha: str = Form(...)):
    # Valida o formulario antes de consultar o usuario e comparar a senha com bcrypt.
    clean_email = normalize_text(email).lower()
    errors: dict[str, str] = {}

    if not validate_email(clean_email):
        errors["email"] = "Informe um email valido."
    if len(senha) < 6:
        errors["senha"] = "A senha deve ter no minimo 6 caracteres."

    if errors:
        return render_template(
            request,
            "login.html",
            {
                "page_title": "Entrar",
                "show_nav": False,
                "body_class": "auth-page",
                "errors": errors,
                "form_data": {"email": clean_email},
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = get_user_by_email(clean_email)
    if not user or not bcrypt.checkpw(senha.encode(), user["senha"].encode()):
        return render_template(
            request,
            "login.html",
            {
                "page_title": "Entrar",
                "show_nav": False,
                "body_class": "auth-page",
                "errors": {"senha": "Email ou senha incorretos."},
                "form_data": {"email": clean_email},
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["user"] = {
        "id_usuario": user["id_usuario"],
        "nome": user["nome"],
        "email": user["email"],
        "tipo": user["tipo"],
    }
    flash(request, f"Bem-vindo(a), {user['nome']}!", "success")
    return redirect_to("/")


@app.get("/cadastro", response_class=HTMLResponse)
def register_page(request: Request):
    if sync_session_user(request):
        return redirect_to("/")
    return render_template(
        request,
        "register.html",
        {
            "page_title": "Criar Conta",
            "show_nav": False,
            "body_class": "auth-page",
            "errors": {},
            "form_data": {"nome": "", "email": "", "tipo": "freelancer"},
        },
    )


@app.post("/cadastro")
def register(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    tipo: str = Form(...),
    senha: str = Form(...),
    confirmar: str = Form(...),
):
    # Guarda os dados normalizados para poder devolver o formulario preenchido em caso de erro.
    form_data = {
        "nome": normalize_text(nome),
        "email": normalize_text(email).lower(),
        "tipo": tipo,
    }
    errors: dict[str, str] = {}

    if len(form_data["nome"]) < 3 or len(form_data["nome"]) > 100:
        errors["nome"] = "O nome deve ter entre 3 e 100 caracteres."
    if not validate_email(form_data["email"]):
        errors["email"] = "Informe um email valido."
    if tipo not in {"empresa", "freelancer"}:
        errors["tipo"] = "Selecione um tipo de conta valido."
    if len(senha) < 6:
        errors["senha"] = "A senha deve ter no minimo 6 caracteres."
    if senha != confirmar:
        errors["confirmar"] = "As senhas nao coincidem."
    if get_user_by_email(form_data["email"]):
        errors["email"] = "Este email ja esta cadastrado."

    if errors:
        return render_template(
            request,
            "register.html",
            {
                "page_title": "Criar Conta",
                "show_nav": False,
                "body_class": "auth-page",
                "errors": errors,
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    hashed_password = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    # Operacoes de escrita usam commit/rollback para manter o banco consistente.
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Usuario (nome, email, senha, tipo)
                VALUES (%s, %s, %s, %s)
                """,
                (form_data["nome"], form_data["email"], hashed_password, tipo),
            )
            new_user_id = cursor.lastrowid
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    request.session["user"] = {
        "id_usuario": new_user_id,
        "nome": form_data["nome"],
        "email": form_data["email"],
        "tipo": tipo,
    }
    flash(request, "Conta criada com sucesso.", "success")
    return redirect_to("/")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Sua sessao foi encerrada.", "info")
    response = redirect_to("/")
    response.headers["Clear-Site-Data"] = '"cache"'
    return response


# Rotas de vagas: criacao, detalhe, candidatura e exclusao.
@app.get("/vaga/nova", response_class=HTMLResponse)
def create_job_page(request: Request):
    user, response = require_user(request, role="empresa")
    if response:
        return response

    return render_template(
        request,
        "create_job.html",
        {
            "page_title": "Publicar Vaga",
            "active_page": "criar",
            "categorias": get_categories(),
            "errors": {},
            "form_data": {
                "titulo": "",
                "local": "",
                "descricao": "",
                "data": date.today().isoformat(),
                "pagamento": "",
                "id_categoria": "",
            },
        },
    )


@app.post("/vaga/nova")
def create_job(
    request: Request,
    titulo: str = Form(...),
    local: str = Form(...),
    descricao: str = Form(...),
    data_servico: str = Form(..., alias="data"),
    pagamento: str = Form(...),
    id_categoria: str = Form(""),
):
    user, response = require_user(request, role="empresa")
    if response:
        return response

    categories = get_categories()
    category_ids = {item["id_categoria"] for item in categories}
    # O formulario e reusado na tela caso alguma validacao falhe.
    form_data = {
        "titulo": normalize_text(titulo),
        "local": normalize_text(local),
        "descricao": normalize_text(descricao),
        "data": data_servico,
        "pagamento": pagamento,
        "id_categoria": id_categoria,
    }
    errors: dict[str, str] = {}

    if len(form_data["titulo"]) < 5 or len(form_data["titulo"]) > 100:
        errors["titulo"] = "O titulo deve ter entre 5 e 100 caracteres."
    if len(form_data["local"]) < 3 or len(form_data["local"]) > 150:
        errors["local"] = "Informe uma localizacao valida."
    if len(form_data["descricao"]) < 20:
        errors["descricao"] = "A descricao deve ter no minimo 20 caracteres."

    parsed_date = parse_future_date(data_servico)
    if not parsed_date:
        errors["data"] = "Selecione uma data valida."
    elif parsed_date < date.today():
        errors["data"] = "A data da vaga nao pode estar no passado."

    try:
        payment_value = Decimal(pagamento)
    except (InvalidOperation, ValueError):
        payment_value = None

    if payment_value is None or payment_value < 0:
        errors["pagamento"] = "Informe um valor de pagamento valido."

    category_value = parse_category(id_categoria)
    if category_value is not None and category_value not in category_ids:
        errors["id_categoria"] = "Categoria invalida."

    if errors:
        return render_template(
            request,
            "create_job.html",
            {
                "page_title": "Publicar Vaga",
                "active_page": "criar",
                "categorias": categories,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Vaga (titulo, descricao, data, local, pagamento, id_empresa, id_categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    form_data["titulo"],
                    form_data["descricao"],
                    parsed_date,
                    form_data["local"],
                    payment_value,
                    user["id_usuario"],
                    category_value,
                ),
            )
            job_id = cursor.lastrowid
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    flash(request, "Vaga publicada com sucesso.", "success")
    return redirect_to(f"/vaga/{job_id}")


@app.get("/vaga/{id_vaga}", response_class=HTMLResponse)
def job_detail(request: Request, id_vaga: int):
    user = sync_session_user(request)
    job = get_job(id_vaga)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga nao encontrada.")

    is_owner = bool(user and user["tipo"] == "empresa" and user["id_usuario"] == job["id_empresa"])
    is_freelancer = bool(user and user["tipo"] == "freelancer")
    # A empresa dona da vaga ve todos os candidatos; freelancer ve apenas seu proprio status.
    applications = get_applications_for_job(id_vaga) if is_owner else []
    stats = get_application_stats(id_vaga, user["id_usuario"] if is_freelancer else None)

    return render_template(
        request,
        "job_detail.html",
        {
            "page_title": job["titulo"],
            "active_page": "vagas",
            "vaga": job,
            "is_owner": is_owner,
            "is_freelancer": is_freelancer,
            "candidaturas": applications,
            "total_candidaturas": stats["total"] if not is_owner else len(applications),
            "ja_candidatado": bool(stats["do_usuario"]) if is_freelancer else False,
        },
    )


@app.post("/vaga/{id_vaga}/candidatar")
def apply_to_job(request: Request, id_vaga: int):
    user, response = require_user(request, role="freelancer")
    if response:
        return response

    job = get_job(id_vaga)
    if not job:
        flash(request, "Vaga nao encontrada.", "error")
        return redirect_to("/")

    # Impede candidatura duplicada do mesmo freelancer na mesma vaga.
    existing_application = query_one(
        """
        SELECT id_candidatura
        FROM Candidatura
        WHERE id_vaga = %s AND id_usuario = %s
        """,
        (id_vaga, user["id_usuario"]),
    )
    if existing_application:
        flash(request, "Voce ja se candidatou a esta vaga.", "error")
        return redirect_to(f"/vaga/{id_vaga}")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Candidatura (id_usuario, id_vaga, status)
                VALUES (%s, %s, 'pendente')
                """,
                (user["id_usuario"], id_vaga),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    flash(request, "Candidatura enviada com sucesso.", "success")
    return redirect_to(f"/vaga/{id_vaga}")


@app.get("/vaga/{id_vaga}/excluir", response_class=HTMLResponse)
def delete_job_page(request: Request, id_vaga: int):
    user, response = require_user(request, role="empresa")
    if response:
        return response

    job = get_job(id_vaga)
    if not job:
        flash(request, "Vaga nao encontrada.", "error")
        return redirect_to("/perfil")
    if user["id_usuario"] != job["id_empresa"]:
        flash(request, "Voce nao pode excluir esta vaga.", "error")
        return redirect_to(f"/vaga/{id_vaga}")

    return render_template(
        request,
        "confirm_action.html",
        {
            "page_title": "Excluir Vaga",
            "active_page": "perfil",
            "card_title": "Excluir vaga",
            "card_message": f'Voce esta prestes a excluir a vaga "{job["titulo"]}".',
            "card_details": "As candidaturas vinculadas tambem serao removidas e a acao nao pode ser desfeita.",
            "confirm_label": "Excluir vaga",
            "cancel_url": f"/vaga/{id_vaga}",
            "confirm_action": f"/vaga/{id_vaga}/excluir",
            "danger": True,
        },
    )


@app.post("/vaga/{id_vaga}/excluir")
def delete_job(request: Request, id_vaga: int):
    user, response = require_user(request, role="empresa")
    if response:
        return response

    job = get_job(id_vaga)
    if not job:
        flash(request, "Vaga nao encontrada.", "error")
        return redirect_to("/perfil")
    if user["id_usuario"] != job["id_empresa"]:
        flash(request, "Voce nao pode excluir esta vaga.", "error")
        return redirect_to(f"/vaga/{id_vaga}")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM Vaga WHERE id_vaga = %s", (id_vaga,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    flash(request, "Vaga excluida com sucesso.", "success")
    return redirect_to("/perfil")


# Rotas de candidaturas: empresa altera o status dos candidatos de suas vagas.
@app.post("/candidaturas/{id_candidatura}/status")
def update_application_status(request: Request, id_candidatura: int, status_candidatura: str = Form(..., alias="status")):
    user, response = require_user(request, role="empresa")
    if response:
        return response

    if status_candidatura not in STATUS_LABELS:
        flash(request, "Status de candidatura invalido.", "error")
        return redirect_to("/perfil")

    # Confirma se a candidatura pertence a uma vaga criada pela empresa logada.
    application = query_one(
        """
        SELECT C.id_candidatura, C.id_vaga, V.id_empresa
        FROM Candidatura AS C
        JOIN Vaga AS V ON V.id_vaga = C.id_vaga
        WHERE C.id_candidatura = %s
        """,
        (id_candidatura,),
    )
    if not application:
        flash(request, "Candidatura nao encontrada.", "error")
        return redirect_to("/perfil")
    if user["id_usuario"] != application["id_empresa"]:
        flash(request, "Voce nao pode alterar esta candidatura.", "error")
        return redirect_to(f"/vaga/{application['id_vaga']}")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE Candidatura SET status = %s WHERE id_candidatura = %s",
                (status_candidatura, id_candidatura),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    flash(request, "Candidatura atualizada.", "success")
    return redirect_to(f"/vaga/{application['id_vaga']}")


# Rotas de perfil: visualizacao, edicao, avatar e exclusao de conta.
@app.get("/perfil", response_class=HTMLResponse)
def profile_page(request: Request):
    user, response = require_user(request)
    if response:
        return response

    return render_template(
        request,
        "profile.html",
        {
            "page_title": "Meu Perfil",
            **build_profile_context(user),
        },
    )


@app.post("/perfil")
def update_profile(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(""),
):
    user, response = require_user(request)
    if response:
        return response

    form_data = {
        "nome": normalize_text(nome),
        "email": normalize_text(email).lower(),
    }
    errors: dict[str, str] = {}

    if len(form_data["nome"]) < 3 or len(form_data["nome"]) > 100:
        errors["nome"] = "O nome deve ter entre 3 e 100 caracteres."
    if not validate_email(form_data["email"]):
        errors["email"] = "Informe um email valido."
    if senha and len(senha) < 6:
        errors["senha"] = "A senha deve ter no minimo 6 caracteres."

    # O email pode ser alterado, mas nao pode colidir com outra conta existente.
    existing_user = query_one(
        """
        SELECT id_usuario
        FROM Usuario
        WHERE email = %s AND id_usuario <> %s
        """,
        (form_data["email"], user["id_usuario"]),
    )
    if existing_user:
        errors["email"] = "Este email ja esta em uso por outra conta."

    if errors:
        return render_template(
            request,
            "profile.html",
            {
                "page_title": "Meu Perfil",
                **build_profile_context(user, form_data=form_data, errors=errors),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if senha:
                # A senha so e atualizada quando o usuario preenche o campo.
                hashed_password = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
                cursor.execute(
                    """
                    UPDATE Usuario
                    SET nome = %s, email = %s, senha = %s
                    WHERE id_usuario = %s
                    """,
                    (form_data["nome"], form_data["email"], hashed_password, user["id_usuario"]),
                )
            else:
                cursor.execute(
                    """
                    UPDATE Usuario
                    SET nome = %s, email = %s
                    WHERE id_usuario = %s
                    """,
                    (form_data["nome"], form_data["email"], user["id_usuario"]),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    request.session["user"] = {
        **user,
        "nome": form_data["nome"],
        "email": form_data["email"],
    }
    flash(request, "Perfil atualizado com sucesso.", "success")
    return redirect_to("/perfil")


@app.post("/perfil/avatar")
async def upload_profile_avatar(request: Request, avatar: UploadFile = File(...)):
    user, response = require_user(request)
    if response:
        return response

    avatar_bytes = await avatar.read()
    avatar_mime = detect_image_mime(avatar_bytes)

    # O avatar fica salvo no banco como bytes, limitado por tamanho e tipo de imagem.
    if not avatar_bytes:
        flash(request, "Selecione uma imagem para enviar.", "error")
        return redirect_to("/perfil")
    if len(avatar_bytes) > MAX_AVATAR_SIZE:
        flash(request, "A imagem deve ter no maximo 2 MB.", "error")
        return redirect_to("/perfil")
    if avatar_mime not in ALLOWED_AVATAR_MIMES:
        flash(request, "Envie uma imagem PNG, JPG, GIF ou WEBP valida.", "error")
        return redirect_to("/perfil")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE Usuario
                SET avatar = %s, avatar_mime = %s
                WHERE id_usuario = %s
                """,
                (avatar_bytes, avatar_mime, user["id_usuario"]),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    flash(request, "Avatar atualizado com sucesso.", "success")
    return redirect_to("/perfil")


@app.get("/perfil/excluir", response_class=HTMLResponse)
def delete_profile_page(request: Request):
    user, response = require_user(request)
    if response:
        return response

    return render_template(
        request,
        "confirm_action.html",
        {
            "page_title": "Excluir Conta",
            "active_page": "perfil",
            "card_title": "Excluir conta",
            "card_message": f'Voce esta prestes a excluir a conta de "{user["nome"]}".',
            "card_details": "Seu perfil, vagas publicadas e candidaturas relacionadas serao removidos definitivamente.",
            "confirm_label": "Excluir conta",
            "cancel_url": "/perfil",
            "confirm_action": "/perfil/excluir",
            "danger": True,
        },
    )


@app.post("/perfil/excluir")
def delete_profile(request: Request):
    user, response = require_user(request)
    if response:
        return response

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (user["id_usuario"],))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    request.session.clear()
    flash(request, "Conta excluida com sucesso.", "success")
    return redirect_to("/")
