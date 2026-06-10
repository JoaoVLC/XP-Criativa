from __future__ import annotations

import base64
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import bcrypt
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymysql.err import IntegrityError
from starlette.middleware.sessions import SessionMiddleware

from app.database import SESSION_SECRET, get_connection

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
DOCUMENT_RE = re.compile(r"^\d+$")
PASSWORD_RE = re.compile(r"^(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
SESSION_SECONDS = 30 * 60

STATUS_LABELS = {"pendente": "Pendente", "aceito": "Aceito", "recusado": "Recusado"}
STATUS_CLASSES = {"pendente": "warning", "aceito": "success", "recusado": "danger"}
JOB_STATUS_LABELS = {"aberta": "Aberta", "pausada": "Pausada", "encerrada": "Encerrada"}

MAX_AVATAR_SIZE = 2 * 1024 * 1024
MAX_RESUME_SIZE = 6 * 1024 * 1024
ALLOWED_AVATAR_MIMES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
ALLOWED_RESUME_MIMES = {"application/pdf"}

app = FastAPI(title="Trampos", version="4.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="trampos_session",
    max_age=SESSION_SECONDS,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def static_asset_url(request: Request, path: str) -> str:
    normalized_path = path.lstrip("/")
    asset_path = STATIC_DIR / normalized_path
    asset_url = str(request.url_for("static", path=normalized_path))
    if asset_path.is_file():
        return f"{asset_url}?v={int(asset_path.stat().st_mtime)}"
    return asset_url


def format_date_br(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y")


def format_datetime_br(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y %H:%M")


def format_money_br(value: Any) -> str:
    if value in (None, ""):
        return ""
    decimal_value = Decimal(str(value))
    formatted = f"{decimal_value:,.2f}"
    return f"R$ {formatted}".replace(",", "X").replace(".", ",").replace("X", ".")


def avatar_initial(name: str | None) -> str:
    return (name or "?").strip()[:1].upper() or "?"


def detect_image_mime(file_bytes: bytes) -> str | None:
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


def detect_resume_mime(file_bytes: bytes) -> str | None:
    if file_bytes.startswith(b"%PDF"):
        return "application/pdf"
    return None


def avatar_data_url(avatar: bytes | None, avatar_mime: str | None) -> str | None:
    if not avatar:
        return None
    mime = avatar_mime or detect_image_mime(avatar) or "image/png"
    encoded = base64.b64encode(avatar).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def enrich_avatar(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    enriched = dict(record)
    enriched["avatar_data"] = avatar_data_url(enriched.get("avatar"), enriched.get("avatar_mime"))
    return enriched


templates.env.filters["date_br"] = format_date_br
templates.env.filters["datetime_br"] = format_datetime_br
templates.env.filters["money_br"] = format_money_br
templates.env.globals["avatar_initial"] = avatar_initial
templates.env.globals["static_asset_url"] = static_asset_url
templates.env.globals["status_label"] = lambda value: STATUS_LABELS.get(value, value)
templates.env.globals["status_class"] = lambda value: STATUS_CLASSES.get(value, "secondary")
templates.env.globals["job_status_label"] = lambda value: JOB_STATUS_LABELS.get(value, value)


def now_ts() -> int:
    return int(datetime.utcnow().timestamp())


def current_user(request: Request) -> dict[str, Any] | None:
    return request.session.get("user")


def flash(request: Request, message: str, kind: str = "info") -> None:
    request.session["flash"] = {"message": message, "type": kind}


def redirect_to(url: str) -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    return apply_response_headers(response)


def apply_response_headers(response: HTMLResponse | RedirectResponse | Response) -> HTMLResponse | RedirectResponse | Response:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


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


def execute_write(query: str, params: tuple[Any, ...] = ()) -> int:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            last_id = cursor.lastrowid
        connection.commit()
        return last_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def normalize_text(value: str) -> str:
    return value.strip()


def normalize_document(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def validate_password(password: str) -> bool:
    return bool(PASSWORD_RE.match(password))


def get_user_by_email(email: str) -> dict[str, Any] | None:
    return query_one("SELECT * FROM Usuario WHERE email = %s", (email,))


def get_user_by_id(id_usuario: int) -> dict[str, Any] | None:
    return query_one(
        """
        SELECT id_usuario, nome, email, tipo, documento_tipo, cpf, cnpj, razao_social,
               curriculo_nome, curriculo_mime, curriculo_enviado_em
        FROM Usuario
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )


def get_user_profile(id_usuario: int) -> dict[str, Any] | None:
    record = query_one(
        """
        SELECT id_usuario, nome, email, tipo, documento_tipo, cpf, cnpj, razao_social,
               avatar, avatar_mime, curriculo_nome, curriculo_mime, curriculo_enviado_em
        FROM Usuario
        WHERE id_usuario = %s
        """,
        (id_usuario,),
    )
    return enrich_avatar(record)


def sync_session_user(request: Request) -> dict[str, Any] | None:
    session_user = current_user(request)
    if not session_user:
        return None
    last_seen = session_user.get("last_seen", 0)
    if now_ts() - last_seen > SESSION_SECONDS:
        request.session.clear()
        flash(request, "Sessão expirada. Faça login novamente para continuar.", "error")
        return None
    db_user = get_user_by_id(session_user["id_usuario"])
    if not db_user:
        request.session.clear()
        flash(request, "Sessão expirada. Faça login novamente para continuar.", "error")
        return None
    session_safe_user = {
        "id_usuario": db_user["id_usuario"],
        "nome": db_user["nome"],
        "email": db_user["email"],
        "tipo": db_user["tipo"],
        "documento_tipo": db_user["documento_tipo"],
        "cpf": db_user.get("cpf"),
        "cnpj": db_user.get("cnpj"),
        "razao_social": db_user.get("razao_social"),
        "last_seen": now_ts(),
    }
    request.session["user"] = session_safe_user
    return session_safe_user


def require_user(request: Request, role: str | None = None) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    user = sync_session_user(request)
    if not user:
        if "flash" not in request.session:
            flash(request, "Faça login para continuar.", "error")
        return None, redirect_to("/login")
    if role and user["tipo"] != role:
        flash(request, "Você não tem permissão para acessar esta página.", "error")
        return None, redirect_to("/")
    return user, None


def require_any_role(request: Request, roles: set[str]) -> tuple[dict[str, Any] | None, RedirectResponse | None]:
    user = sync_session_user(request)
    if not user:
        flash(request, "Faça login para continuar.", "error")
        return None, redirect_to("/login")
    if user["tipo"] not in roles:
        flash(request, "Você não tem permissão para acessar esta página.", "error")
        return None, redirect_to("/")
    return user, None


def unread_notifications_count(id_usuario: int) -> int:
    row = query_one("SELECT COUNT(*) AS total FROM Notificacao WHERE id_usuario = %s AND lida = 0", (id_usuario,))
    return int(row["total"] if row else 0)


def create_notification(id_usuario: int | None, titulo: str, mensagem: str, tipo: str = "info") -> None:
    if not id_usuario:
        return
    execute_write(
        """
        INSERT INTO Notificacao (id_usuario, titulo, mensagem, tipo)
        VALUES (%s, %s, %s, %s)
        """,
        (id_usuario, titulo, mensagem, tipo),
    )


def render_template(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    user = sync_session_user(request)
    user_profile = get_user_profile(user["id_usuario"]) if user else None
    payload = {
        "request": request,
        "user": user,
        "user_avatar_data": user_profile["avatar_data"] if user_profile else None,
        "unread_notifications": unread_notifications_count(user["id_usuario"]) if user else 0,
        "flash": request.session.pop("flash", None),
        "active_page": "",
        "page_title": "Trampos",
        "show_nav": True,
    }
    if context:
        payload.update(context)
    response = templates.TemplateResponse(request=request, name=template_name, context=payload, status_code=status_code)
    return apply_response_headers(response)


def get_categories() -> list[dict[str, Any]]:
    return query_all("SELECT id_categoria, nome FROM Categoria ORDER BY nome")


def get_companies() -> list[dict[str, Any]]:
    return query_all("SELECT id_usuario, COALESCE(razao_social, nome) AS nome FROM Usuario WHERE tipo = 'empresa' ORDER BY nome")


def get_jobs(
    *,
    search: str = "",
    category_id: int | None = None,
    company_id: int | None = None,
    location: str = "",
    status_value: str = "",
) -> list[dict[str, Any]]:
    sql = """
        SELECT V.id_vaga, V.titulo, V.descricao, V.data, V.local, V.pagamento, V.status,
               V.id_empresa, V.id_categoria, COALESCE(U.razao_social, U.nome) AS empresa_nome,
               C.nome AS categoria_nome
        FROM Vaga AS V
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
    """
    conditions: list[str] = []
    params: list[Any] = []
    if search:
        like = f"%{search}%"
        conditions.append("(V.titulo LIKE %s OR V.descricao LIKE %s OR U.nome LIKE %s OR U.razao_social LIKE %s)")
        params.extend([like, like, like, like])
    if location:
        conditions.append("V.local LIKE %s")
        params.append(f"%{location}%")
    if category_id:
        conditions.append("V.id_categoria = %s")
        params.append(category_id)
    if company_id:
        conditions.append("V.id_empresa = %s")
        params.append(company_id)
    if status_value in JOB_STATUS_LABELS:
        conditions.append("V.status = %s")
        params.append(status_value)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY V.data ASC, V.id_vaga DESC"
    return query_all(sql, tuple(params))


def get_job(id_vaga: int) -> dict[str, Any] | None:
    return query_one(
        """
        SELECT V.id_vaga, V.titulo, V.descricao, V.data, V.local, V.pagamento, V.status,
               V.id_empresa, V.id_categoria, COALESCE(U.razao_social, U.nome) AS empresa_nome,
               U.email AS empresa_email, C.nome AS categoria_nome
        FROM Vaga AS V
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
        WHERE V.id_vaga = %s
        """,
        (id_vaga,),
    )


def get_applications_for_job(id_vaga: int) -> list[dict[str, Any]]:
    records = query_all(
        """
        SELECT C.id_candidatura, C.id_usuario, C.id_vaga, C.status, C.criada_em,
               U.nome AS usuario_nome, U.email AS usuario_email, U.avatar, U.avatar_mime,
               U.curriculo_nome, U.curriculo_enviado_em
        FROM Candidatura AS C
        JOIN Usuario AS U ON U.id_usuario = C.id_usuario
        WHERE C.id_vaga = %s
        ORDER BY CASE C.status WHEN 'pendente' THEN 0 WHEN 'aceito' THEN 1 ELSE 2 END, C.criada_em DESC
        """,
        (id_vaga,),
    )
    return [enrich_avatar(record) for record in records]


def get_application_stats(id_vaga: int, id_usuario: int | None = None) -> dict[str, Any]:
    return query_one(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN id_usuario = %s THEN 1 ELSE 0 END) AS do_usuario
        FROM Candidatura
        WHERE id_vaga = %s
        """,
        (id_usuario or 0, id_vaga),
    ) or {"total": 0, "do_usuario": 0}


def get_company_jobs(id_empresa: int) -> list[dict[str, Any]]:
    return query_all(
        """
        SELECT V.id_vaga, V.titulo, V.local, V.data, V.pagamento, V.status,
               C.nome AS categoria_nome, COUNT(A.id_candidatura) AS total_candidaturas
        FROM Vaga AS V
        LEFT JOIN Categoria AS C ON C.id_categoria = V.id_categoria
        LEFT JOIN Candidatura AS A ON A.id_vaga = V.id_vaga
        WHERE V.id_empresa = %s
        GROUP BY V.id_vaga, V.titulo, V.local, V.data, V.pagamento, V.status, C.nome
        ORDER BY V.data ASC, V.id_vaga DESC
        """,
        (id_empresa,),
    )


def get_user_applications(id_usuario: int) -> list[dict[str, Any]]:
    return query_all(
        """
        SELECT C.id_candidatura, C.status, C.id_vaga, C.criada_em,
               V.titulo, V.local, V.data, V.pagamento, V.status AS vaga_status,
               COALESCE(U.razao_social, U.nome) AS empresa_nome, C2.nome AS categoria_nome
        FROM Candidatura AS C
        JOIN Vaga AS V ON V.id_vaga = C.id_vaga
        JOIN Usuario AS U ON U.id_usuario = V.id_empresa
        LEFT JOIN Categoria AS C2 ON C2.id_categoria = V.id_categoria
        WHERE C.id_usuario = %s
        ORDER BY C.criada_em DESC
        """,
        (id_usuario,),
    )


def parse_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_future_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def form_context(user: dict[str, Any], form_data: dict[str, Any] | None = None, errors: dict[str, str] | None = None) -> dict[str, Any]:
    profile_user = get_user_profile(user["id_usuario"]) or dict(user)
    return {
        "active_page": "perfil",
        "page_title": "Meu Perfil",
        "form_data": form_data or {
            "nome": profile_user["nome"],
            "email": profile_user["email"],
            "cpf": profile_user.get("cpf") or "",
            "cnpj": profile_user.get("cnpj") or "",
            "razao_social": profile_user.get("razao_social") or "",
        },
        "errors": errors or {},
        "profile_user": profile_user,
        "jobs": get_company_jobs(user["id_usuario"]) if user["tipo"] == "empresa" else [],
        "applications": get_user_applications(user["id_usuario"]) if user["tipo"] == "freelancer" else [],
    }


async def read_resume_file(resume: UploadFile | None) -> tuple[bytes | None, str | None, str | None, str | None]:
    if not resume or not resume.filename:
        return None, None, None, None
    resume_bytes = await resume.read()
    resume_mime = detect_resume_mime(resume_bytes)
    if not resume_bytes:
        return None, None, None, "Selecione um arquivo de currículo."
    if len(resume_bytes) > MAX_RESUME_SIZE:
        return None, None, None, "O currículo deve ter no máximo 6 MB."
    if resume_mime not in ALLOWED_RESUME_MIMES:
        return None, None, None, "Envie o currículo em PDF."
    return resume_bytes, resume.filename[:180], resume_mime, None


@app.get("/", response_class=HTMLResponse)
def home(request: Request, busca: str = "", categoria: str = "", empresa: str = "", local: str = "", situacao: str = "aberta"):
    categories = get_categories()
    companies = get_companies()
    jobs = get_jobs(
        search=normalize_text(busca),
        category_id=parse_int(categoria),
        company_id=parse_int(empresa),
        location=normalize_text(local),
        status_value=situacao,
    )
    return render_template(
        request,
        "index.html",
        {
            "page_title": "Vagas disponíveis",
            "active_page": "vagas",
            "categorias": categories,
            "empresas": companies,
            "vagas": jobs,
            "job_statuses": JOB_STATUS_LABELS,
            "filtros": {"busca": busca, "categoria": categoria, "empresa": empresa, "local": local, "situacao": situacao},
        },
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if sync_session_user(request):
        return redirect_to("/")
    return render_template(request, "login.html", {"page_title": "Entrar", "show_nav": False, "body_class": "auth-page", "errors": {}, "form_data": {"email": ""}})


@app.post("/login")
def login(request: Request, email: str = Form(...), senha: str = Form(...)):
    clean_email = normalize_text(email).lower()
    errors: dict[str, str] = {}
    if not validate_email(clean_email):
        errors["email"] = "Informe um email válido."
    if not senha:
        errors["senha"] = "Informe sua senha."
    if errors:
        return render_template(request, "login.html", {"page_title": "Entrar", "show_nav": False, "body_class": "auth-page", "errors": errors, "form_data": {"email": clean_email}}, status_code=400)
    user = get_user_by_email(clean_email)
    if not user or not bcrypt.checkpw(senha.encode(), user["senha"].encode()):
        return render_template(request, "login.html", {"page_title": "Entrar", "show_nav": False, "body_class": "auth-page", "errors": {"senha": "Email ou senha incorretos."}, "form_data": {"email": clean_email}}, status_code=401)
    request.session["user"] = {key: user[key] for key in ("id_usuario", "nome", "email", "tipo", "documento_tipo", "cpf", "cnpj", "razao_social")}
    request.session["user"]["last_seen"] = now_ts()
    flash(request, f"Login realizado. Bem-vindo(a), {user['nome']}!", "success")
    return redirect_to("/admin" if user["tipo"] == "admin" else "/")


@app.get("/cadastro", response_class=HTMLResponse)
def register_page(request: Request):
    if sync_session_user(request):
        return redirect_to("/")
    return render_template(request, "register.html", {"page_title": "Criar conta", "show_nav": False, "body_class": "auth-page", "errors": {}, "form_data": {"nome": "", "razao_social": "", "cpf": "", "cnpj": "", "email": "", "tipo": "freelancer"}})


@app.post("/cadastro")
async def register(
    request: Request,
    nome: str = Form(""),
    razao_social: str = Form(""),
    cpf: str = Form(""),
    cnpj: str = Form(""),
    email: str = Form(...),
    tipo: str = Form(...),
    senha: str = Form(...),
    confirmar: str = Form(...),
    curriculo: UploadFile | None = File(None),
):
    clean_tipo = tipo if tipo in {"freelancer", "empresa"} else "freelancer"
    clean_cpf = normalize_document(cpf)
    clean_cnpj = normalize_document(cnpj)
    form_data = {
        "nome": normalize_text(nome),
        "razao_social": normalize_text(razao_social),
        "cpf": clean_cpf,
        "cnpj": clean_cnpj,
        "email": normalize_text(email).lower(),
        "tipo": clean_tipo,
    }
    errors: dict[str, str] = {}
    if clean_tipo == "freelancer":
        if len(form_data["nome"]) < 3:
            errors["nome"] = "Informe seu nome completo."
        if not clean_cpf or not DOCUMENT_RE.match(clean_cpf):
            errors["cpf"] = "CPF obrigatório. Use apenas números."
    if clean_tipo == "empresa":
        if len(form_data["razao_social"]) < 3:
            errors["razao_social"] = "Informe a razão social."
        if not clean_cnpj or not DOCUMENT_RE.match(clean_cnpj):
            errors["cnpj"] = "CNPJ obrigatório. Use apenas números."
    if not validate_email(form_data["email"]):
        errors["email"] = "Informe um email válido."
    if not validate_password(senha):
        errors["senha"] = "Use 8 caracteres, 1 número e 1 caractere especial."
    if senha != confirmar:
        errors["confirmar"] = "As senhas não coincidem."
    if get_user_by_email(form_data["email"]):
        errors["email"] = "Este email já está cadastrado."
    if clean_cpf and query_one("SELECT id_usuario FROM Usuario WHERE cpf = %s", (clean_cpf,)):
        errors["cpf"] = "Este CPF já está cadastrado."
    if clean_cnpj and query_one("SELECT id_usuario FROM Usuario WHERE cnpj = %s", (clean_cnpj,)):
        errors["cnpj"] = "Este CNPJ já está cadastrado."
    resume_bytes, resume_name, resume_mime, resume_error = await read_resume_file(curriculo)
    if clean_tipo == "freelancer" and resume_error:
        errors["curriculo"] = resume_error
    if clean_tipo == "freelancer" and not resume_bytes and not errors.get("curriculo"):
        errors["curriculo"] = "Currículo em PDF obrigatório para pessoa física."
    if errors:
        return render_template(request, "register.html", {"page_title": "Criar conta", "show_nav": False, "body_class": "auth-page", "errors": errors, "form_data": form_data}, status_code=400)
    hashed_password = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    display_name = form_data["nome"] if clean_tipo == "freelancer" else form_data["razao_social"]
    try:
        new_user_id = execute_write(
            """
            INSERT INTO Usuario (nome, email, senha, tipo, documento_tipo, cpf, cnpj, razao_social,
                                 curriculo, curriculo_nome, curriculo_mime, curriculo_enviado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s IS NULL, NULL, NOW()))
            """,
            (display_name, form_data["email"], hashed_password, clean_tipo, "cpf" if clean_tipo == "freelancer" else "cnpj", clean_cpf or None, clean_cnpj or None, form_data["razao_social"] or None, resume_bytes, resume_name, resume_mime, resume_bytes),
        )
    except IntegrityError:
        errors["email"] = "Documento ou email já cadastrado."
        return render_template(request, "register.html", {"page_title": "Criar conta", "show_nav": False, "body_class": "auth-page", "errors": errors, "form_data": form_data}, status_code=400)
    request.session["user"] = {"id_usuario": new_user_id, "nome": display_name, "email": form_data["email"], "tipo": clean_tipo, "documento_tipo": "cpf" if clean_tipo == "freelancer" else "cnpj", "cpf": clean_cpf or None, "cnpj": clean_cnpj or None, "razao_social": form_data["razao_social"] or None, "last_seen": now_ts()}
    create_notification(new_user_id, "Cadastro realizado", "Seu perfil foi criado com sucesso.", "success")
    flash(request, "Cadastro realizado com sucesso.", "success")
    return redirect_to("/")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Sua sessao foi encerrada.", "info")
    response = redirect_to("/")
    response.headers["Clear-Site-Data"] = '"cache"'
    return response


@app.get("/vaga/nova", response_class=HTMLResponse)
def create_job_page(request: Request):
    user, response = require_user(request, role="empresa")
    if response:
        return response
    return job_form_response(request, user, "create_job.html", "Publicar Vaga", "/vaga/nova")


def job_form_response(request: Request, user: dict[str, Any], template_name: str, title: str, action: str, job: dict[str, Any] | None = None, errors: dict[str, str] | None = None, status_code: int = 200):
    data = job or {"titulo": "", "local": "", "descricao": "", "data": date.today().isoformat(), "pagamento": "", "id_categoria": "", "status": "aberta"}
    return render_template(request, template_name, {"page_title": title, "active_page": "criar", "categorias": get_categories(), "job_statuses": JOB_STATUS_LABELS, "errors": errors or {}, "form_data": data, "form_action": action, "submit_label": title}, status_code=status_code)


def validate_job_form(titulo: str, local: str, descricao: str, data_servico: str, pagamento: str, id_categoria: str, status_value: str) -> tuple[dict[str, Any], dict[str, str]]:
    form_data = {"titulo": normalize_text(titulo), "local": normalize_text(local), "descricao": normalize_text(descricao), "data": data_servico, "pagamento": pagamento, "id_categoria": id_categoria, "status": status_value}
    errors: dict[str, str] = {}
    if len(form_data["titulo"]) < 5:
        errors["titulo"] = "O título deve ter pelo menos 5 caracteres."
    if len(form_data["local"]) < 3:
        errors["local"] = "Informe uma localização válida."
    if len(form_data["descricao"]) < 20:
        errors["descricao"] = "A descrição deve ter no mínimo 20 caracteres."
    parsed_date = parse_future_date(data_servico)
    if not parsed_date:
        errors["data"] = "Selecione uma data valida."
    elif parsed_date < date.today():
        errors["data"] = "A data da vaga não pode estar no passado."
    try:
        payment_value = Decimal(pagamento)
    except (InvalidOperation, ValueError):
        payment_value = None
    if payment_value is None or payment_value < 0:
        errors["pagamento"] = "Informe um valor de pagamento válido."
    category_value = parse_int(id_categoria)
    category_ids = {item["id_categoria"] for item in get_categories()}
    if category_value is not None and category_value not in category_ids:
        errors["id_categoria"] = "Categoria invalida."
    if status_value not in JOB_STATUS_LABELS:
        errors["status"] = "Status de vaga inválido."
    form_data["_parsed_date"] = parsed_date
    form_data["_payment_value"] = payment_value
    form_data["_category_value"] = category_value
    return form_data, errors


@app.post("/vaga/nova")
def create_job(request: Request, titulo: str = Form(...), local: str = Form(...), descricao: str = Form(...), data_servico: str = Form(..., alias="data"), pagamento: str = Form(...), id_categoria: str = Form(""), status_vaga: str = Form("aberta", alias="status")):
    user, response = require_user(request, role="empresa")
    if response:
        return response
    form_data, errors = validate_job_form(titulo, local, descricao, data_servico, pagamento, id_categoria, status_vaga)
    if errors:
        return job_form_response(request, user, "create_job.html", "Publicar Vaga", "/vaga/nova", form_data, errors, 400)
    job_id = execute_write(
        """
        INSERT INTO Vaga (titulo, descricao, data, local, pagamento, status, id_empresa, id_categoria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (form_data["titulo"], form_data["descricao"], form_data["_parsed_date"], form_data["local"], form_data["_payment_value"], status_vaga, user["id_usuario"], form_data["_category_value"]),
    )
    create_notification(user["id_usuario"], "Nova vaga publicada", f"A vaga {form_data['titulo']} foi publicada.", "success")
    flash(request, "Vaga publicada com sucesso.", "success")
    return redirect_to(f"/vaga/{job_id}")


@app.get("/vaga/{id_vaga}/editar", response_class=HTMLResponse)
def edit_job_page(request: Request, id_vaga: int):
    user, response = require_user(request, role="empresa")
    if response:
        return response
    job = get_job(id_vaga)
    if not job or job["id_empresa"] != user["id_usuario"]:
        flash(request, "Vaga não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    return job_form_response(request, user, "create_job.html", "Editar Vaga", f"/vaga/{id_vaga}/editar", job)


@app.post("/vaga/{id_vaga}/editar")
def edit_job(request: Request, id_vaga: int, titulo: str = Form(...), local: str = Form(...), descricao: str = Form(...), data_servico: str = Form(..., alias="data"), pagamento: str = Form(...), id_categoria: str = Form(""), status_vaga: str = Form("aberta", alias="status")):
    user, response = require_user(request, role="empresa")
    if response:
        return response
    job = get_job(id_vaga)
    if not job or job["id_empresa"] != user["id_usuario"]:
        flash(request, "Vaga não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    form_data, errors = validate_job_form(titulo, local, descricao, data_servico, pagamento, id_categoria, status_vaga)
    if errors:
        return job_form_response(request, user, "create_job.html", "Editar Vaga", f"/vaga/{id_vaga}/editar", form_data, errors, 400)
    execute_write(
        """
        UPDATE Vaga
        SET titulo = %s, descricao = %s, data = %s, local = %s, pagamento = %s, status = %s, id_categoria = %s
        WHERE id_vaga = %s AND id_empresa = %s
        """,
        (form_data["titulo"], form_data["descricao"], form_data["_parsed_date"], form_data["local"], form_data["_payment_value"], status_vaga, form_data["_category_value"], id_vaga, user["id_usuario"]),
    )
    flash(request, "Vaga atualizada com sucesso.", "success")
    return redirect_to(f"/vaga/{id_vaga}")


@app.get("/vaga/{id_vaga}", response_class=HTMLResponse)
def job_detail(request: Request, id_vaga: int):
    user = sync_session_user(request)
    job = get_job(id_vaga)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    is_owner = bool(user and user["tipo"] in {"empresa", "admin"} and (user["tipo"] == "admin" or user["id_usuario"] == job["id_empresa"]))
    is_freelancer = bool(user and user["tipo"] == "freelancer")
    applications = get_applications_for_job(id_vaga) if is_owner else []
    stats = get_application_stats(id_vaga, user["id_usuario"] if is_freelancer else None)
    profile = get_user_profile(user["id_usuario"]) if is_freelancer and user else None
    return render_template(request, "job_detail.html", {"page_title": job["titulo"], "active_page": "vagas", "vaga": job, "is_owner": is_owner, "is_freelancer": is_freelancer, "candidaturas": applications, "total_candidaturas": stats["total"] if not is_owner else len(applications), "ja_candidatado": bool(stats["do_usuario"]) if is_freelancer else False, "has_resume": bool(profile and profile.get("curriculo_nome"))})


@app.post("/vaga/{id_vaga}/candidatar")
def apply_to_job(request: Request, id_vaga: int):
    user, response = require_user(request, role="freelancer")
    if response:
        return response
    profile = get_user_profile(user["id_usuario"])
    if not profile or not profile.get("curriculo_nome"):
        flash(request, "Cadastre um currículo em PDF antes de se candidatar.", "error")
        return redirect_to("/perfil")
    job = get_job(id_vaga)
    if not job or job["status"] != "aberta":
        flash(request, "Vaga indisponivel para candidatura.", "error")
        return redirect_to("/")
    if query_one("SELECT id_candidatura FROM Candidatura WHERE id_vaga = %s AND id_usuario = %s", (id_vaga, user["id_usuario"])):
        flash(request, "Você já se candidatou a esta vaga.", "error")
        return redirect_to(f"/vaga/{id_vaga}")
    app_id = execute_write("INSERT INTO Candidatura (id_usuario, id_vaga, status) VALUES (%s, %s, 'pendente')", (user["id_usuario"], id_vaga))
    create_notification(user["id_usuario"], "Candidatura enviada", f"Você se candidatou à vaga {job['titulo']}.", "success")
    create_notification(job["id_empresa"], "Novo candidato inscrito", f"{user['nome']} se candidatou a vaga {job['titulo']}.", "info")
    flash(request, "Candidatura enviada com sucesso.", "success")
    return redirect_to(f"/vaga/{id_vaga}")


@app.post("/candidaturas/{id_candidatura}/status")
def update_application_status(request: Request, id_candidatura: int, status_candidatura: str = Form(..., alias="status")):
    user, response = require_any_role(request, {"empresa", "admin"})
    if response:
        return response
    if status_candidatura not in STATUS_LABELS:
        flash(request, "Status de candidatura inválido.", "error")
        return redirect_to("/perfil")
    application = query_one(
        """
        SELECT C.id_candidatura, C.id_vaga, C.id_usuario, V.id_empresa, V.titulo
        FROM Candidatura AS C JOIN Vaga AS V ON V.id_vaga = C.id_vaga
        WHERE C.id_candidatura = %s
        """,
        (id_candidatura,),
    )
    if not application or (user["tipo"] != "admin" and user["id_usuario"] != application["id_empresa"]):
        flash(request, "Candidatura não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    execute_write("UPDATE Candidatura SET status = %s, atualizada_em = NOW() WHERE id_candidatura = %s", (status_candidatura, id_candidatura))
    create_notification(application["id_usuario"], f"Candidatura {STATUS_LABELS[status_candidatura].lower()}", f"Sua candidatura para {application['titulo']} foi atualizada.", "info")
    flash(request, "Candidatura atualizada.", "success")
    return redirect_to(f"/vaga/{application['id_vaga']}")


@app.post("/candidaturas/{id_candidatura}/excluir")
def delete_application(request: Request, id_candidatura: int):
    user, response = require_user(request)
    if response:
        return response
    app_row = query_one(
        """
        SELECT C.id_candidatura, C.id_usuario, C.id_vaga, V.id_empresa
        FROM Candidatura C JOIN Vaga V ON V.id_vaga = C.id_vaga
        WHERE C.id_candidatura = %s
        """,
        (id_candidatura,),
    )
    if not app_row or (user["tipo"] != "admin" and user["id_usuario"] not in {app_row["id_usuario"], app_row["id_empresa"]}):
        flash(request, "Candidatura não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    execute_write("DELETE FROM Candidatura WHERE id_candidatura = %s", (id_candidatura,))
    flash(request, "Candidatura removida com sucesso.", "success")
    return redirect_to("/perfil" if user["tipo"] == "freelancer" else f"/vaga/{app_row['id_vaga']}")


@app.get("/vaga/{id_vaga}/excluir", response_class=HTMLResponse)
def delete_job_page(request: Request, id_vaga: int):
    user, response = require_any_role(request, {"empresa", "admin"})
    if response:
        return response
    job = get_job(id_vaga)
    if not job or (user["tipo"] != "admin" and user["id_usuario"] != job["id_empresa"]):
        flash(request, "Vaga não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    return render_template(request, "confirm_action.html", {"page_title": "Excluir vaga", "active_page": "perfil", "card_title": "Excluir vaga", "card_message": f'Você está prestes a excluir a vaga "{job["titulo"]}".', "card_details": "As candidaturas vinculadas também serão removidas.", "confirm_label": "Excluir vaga", "cancel_url": f"/vaga/{id_vaga}", "confirm_action": f"/vaga/{id_vaga}/excluir", "danger": True})


@app.post("/vaga/{id_vaga}/excluir")
def delete_job(request: Request, id_vaga: int):
    user, response = require_any_role(request, {"empresa", "admin"})
    if response:
        return response
    job = get_job(id_vaga)
    if not job or (user["tipo"] != "admin" and user["id_usuario"] != job["id_empresa"]):
        flash(request, "Vaga não encontrada ou sem permissão.", "error")
        return redirect_to("/perfil")
    execute_write("DELETE FROM Vaga WHERE id_vaga = %s", (id_vaga,))
    flash(request, "Vaga removida com sucesso.", "success")
    return redirect_to("/admin" if user["tipo"] == "admin" else "/perfil")


@app.get("/perfil", response_class=HTMLResponse)
def profile_page(request: Request):
    user, response = require_user(request)
    if response:
        return response
    return render_template(request, "profile.html", {"page_title": "Meu Perfil", **form_context(user)})


@app.get("/perfil/visualizar", response_class=HTMLResponse)
def self_profile_page(request: Request):
    user, response = require_user(request)
    if response:
        return response
    return render_template(request, "self_profile.html", {"page_title": "Ver Perfil", **form_context(user)})


@app.post("/perfil")
def update_profile(request: Request, nome: str = Form(""), razao_social: str = Form(""), email: str = Form(...), cpf: str = Form(""), cnpj: str = Form(""), senha: str = Form("")):
    user, response = require_user(request)
    if response:
        return response
    clean_email = normalize_text(email).lower()
    clean_cpf = normalize_document(cpf)
    clean_cnpj = normalize_document(cnpj)
    form_data = {"nome": normalize_text(nome), "razao_social": normalize_text(razao_social), "email": clean_email, "cpf": clean_cpf, "cnpj": clean_cnpj}
    errors: dict[str, str] = {}
    if user["tipo"] == "empresa":
        if len(form_data["razao_social"]) < 3:
            errors["razao_social"] = "Informe a razão social."
        if not clean_cnpj:
            errors["cnpj"] = "CNPJ obrigatorio."
    else:
        if len(form_data["nome"]) < 3:
            errors["nome"] = "Informe seu nome."
        if user["tipo"] == "freelancer" and not clean_cpf:
            errors["cpf"] = "CPF obrigatorio."
    if not validate_email(clean_email):
        errors["email"] = "Informe um email válido."
    if senha and not validate_password(senha):
        errors["senha"] = "Use 8 caracteres, 1 número e 1 caractere especial."
    for field, value in {"email": clean_email, "cpf": clean_cpf, "cnpj": clean_cnpj}.items():
        if value and query_one(f"SELECT id_usuario FROM Usuario WHERE {field} = %s AND id_usuario <> %s", (value, user["id_usuario"])):
            errors[field] = f"Este {field.upper()} já está em uso." if field != "email" else "Este email já está em uso."
    if errors:
        return render_template(request, "profile.html", {"page_title": "Meu Perfil", **form_context(user, form_data, errors)}, status_code=400)
    display_name = form_data["razao_social"] if user["tipo"] == "empresa" else form_data["nome"]
    if senha:
        hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        execute_write("UPDATE Usuario SET nome = %s, razao_social = %s, email = %s, cpf = %s, cnpj = %s, senha = %s WHERE id_usuario = %s", (display_name, form_data["razao_social"] or None, clean_email, clean_cpf or None, clean_cnpj or None, hashed, user["id_usuario"]))
    else:
        execute_write("UPDATE Usuario SET nome = %s, razao_social = %s, email = %s, cpf = %s, cnpj = %s WHERE id_usuario = %s", (display_name, form_data["razao_social"] or None, clean_email, clean_cpf or None, clean_cnpj or None, user["id_usuario"]))
    request.session["user"] = {**user, "nome": display_name, "email": clean_email, "cpf": clean_cpf or None, "cnpj": clean_cnpj or None, "razao_social": form_data["razao_social"] or None, "last_seen": now_ts()}
    flash(request, "Perfil atualizado com sucesso.", "success")
    return redirect_to("/perfil")


@app.post("/perfil/avatar")
async def upload_profile_avatar(request: Request, avatar: UploadFile = File(...)):
    user, response = require_user(request)
    if response:
        return response
    avatar_bytes = await avatar.read()
    avatar_mime = detect_image_mime(avatar_bytes)
    if not avatar_bytes:
        flash(request, "Selecione uma imagem para enviar.", "error")
    elif len(avatar_bytes) > MAX_AVATAR_SIZE:
        flash(request, "A imagem deve ter no maximo 2 MB.", "error")
    elif avatar_mime not in ALLOWED_AVATAR_MIMES:
        flash(request, "Envie uma imagem PNG, JPG, GIF ou WEBP valida.", "error")
    else:
        execute_write("UPDATE Usuario SET avatar = %s, avatar_mime = %s WHERE id_usuario = %s", (avatar_bytes, avatar_mime, user["id_usuario"]))
        flash(request, "Avatar atualizado com sucesso.", "success")
    return redirect_to("/perfil")


@app.post("/perfil/curriculo")
async def upload_resume(request: Request, curriculo: UploadFile = File(...)):
    user, response = require_user(request, role="freelancer")
    if response:
        return response
    resume_bytes, resume_name, resume_mime, resume_error = await read_resume_file(curriculo)
    if resume_error:
        flash(request, resume_error, "error")
        return redirect_to("/perfil")
    execute_write("UPDATE Usuario SET curriculo = %s, curriculo_nome = %s, curriculo_mime = %s, curriculo_enviado_em = NOW() WHERE id_usuario = %s", (resume_bytes, resume_name, resume_mime, user["id_usuario"]))
    flash(request, "Currículo atualizado com sucesso.", "success")
    return redirect_to("/perfil")


def can_view_resume(user: dict[str, Any], candidate_id: int) -> bool:
    if user["tipo"] == "admin" or user["id_usuario"] == candidate_id:
        return True
    if user["tipo"] != "empresa":
        return False
    row = query_one(
        """
        SELECT C.id_candidatura
        FROM Candidatura C JOIN Vaga V ON V.id_vaga = C.id_vaga
        WHERE C.id_usuario = %s AND V.id_empresa = %s
        LIMIT 1
        """,
        (candidate_id, user["id_usuario"]),
    )
    return bool(row)


@app.get("/usuarios/{id_usuario}/curriculo")
def download_resume(request: Request, id_usuario: int):
    user, response = require_user(request)
    if response:
        return response
    if not can_view_resume(user, id_usuario):
        raise HTTPException(status_code=403, detail="Sem permissão.")
    candidate = query_one("SELECT nome, curriculo, curriculo_nome, curriculo_mime FROM Usuario WHERE id_usuario = %s", (id_usuario,))
    if not candidate or not candidate.get("curriculo"):
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")
    create_notification(id_usuario, "Empresa visualizou seu perfil", f"{user['nome']} acessou seu currículo.", "info") if user["tipo"] == "empresa" else None
    filename = candidate.get("curriculo_nome") or f"curriculo-{id_usuario}.pdf"
    return Response(content=candidate["curriculo"], media_type=candidate.get("curriculo_mime") or "application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/candidato/{id_usuario}", response_class=HTMLResponse)
def candidate_history(request: Request, id_usuario: int):
    user, response = require_any_role(request, {"empresa", "admin"})
    if response:
        return response
    if user["tipo"] != "admin" and not can_view_resume(user, id_usuario):
        flash(request, "Você só pode visualizar candidatos das suas vagas.", "error")
        return redirect_to("/perfil")
    candidate = get_user_profile(id_usuario)
    if not candidate or candidate["tipo"] != "freelancer":
        flash(request, "Candidato não encontrado.", "error")
        return redirect_to("/perfil")
    history = get_user_applications(id_usuario)
    create_notification(id_usuario, "Empresa visualizou seu perfil", f"{user['nome']} consultou seu historico.", "info") if user["tipo"] == "empresa" else None
    return render_template(request, "candidate.html", {"page_title": "Histórico do candidato", "candidate": candidate, "applications": history})


@app.get("/perfil/excluir", response_class=HTMLResponse)
def delete_profile_page(request: Request):
    user, response = require_user(request)
    if response:
        return response
    return render_template(request, "confirm_action.html", {"page_title": "Excluir conta", "active_page": "perfil", "card_title": "Excluir conta", "card_message": f'Você está prestes a excluir a conta de "{user["nome"]}".', "card_details": "Seu perfil, vagas e candidaturas relacionadas serão removidos definitivamente.", "confirm_label": "Excluir conta", "cancel_url": "/perfil", "confirm_action": "/perfil/excluir", "danger": True})


@app.post("/perfil/excluir")
def delete_profile(request: Request):
    user, response = require_user(request)
    if response:
        return response
    execute_write("DELETE FROM Usuario WHERE id_usuario = %s", (user["id_usuario"],))
    request.session.clear()
    flash(request, "Conta excluída com sucesso.", "success")
    return redirect_to("/")


@app.get("/notificacoes", response_class=HTMLResponse)
def notifications_page(request: Request):
    user, response = require_user(request)
    if response:
        return response
    notifications = query_all("SELECT * FROM Notificacao WHERE id_usuario = %s ORDER BY criada_em DESC", (user["id_usuario"],))
    execute_write("UPDATE Notificacao SET lida = 1 WHERE id_usuario = %s", (user["id_usuario"],))
    return render_template(request, "notifications.html", {"page_title": "Notificações", "active_page": "notificacoes", "notifications": notifications})


@app.post("/notificacoes/limpar")
def clear_notifications(request: Request):
    user, response = require_user(request)
    if response:
        return response
    execute_write("DELETE FROM Notificacao WHERE id_usuario = %s", (user["id_usuario"],))
    flash(request, "Notificações removidas.", "success")
    return redirect_to("/notificacoes")


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    user, response = require_user(request, role="admin")
    if response:
        return response
    users = query_all("SELECT * FROM Usuario ORDER BY tipo, nome")
    jobs = get_jobs(status_value="")
    applications = query_all(
        """
        SELECT C.*, U.nome AS candidato_nome, V.titulo AS vaga_titulo
        FROM Candidatura C
        JOIN Usuario U ON U.id_usuario = C.id_usuario
        JOIN Vaga V ON V.id_vaga = C.id_vaga
        ORDER BY C.criada_em DESC
        """
    )
    stats = {"usuarios": len([u for u in users if u["tipo"] == "freelancer"]), "empresas": len([u for u in users if u["tipo"] == "empresa"]), "vagas": len(jobs), "candidaturas": len(applications)}
    return render_template(request, "admin.html", {"page_title": "Administrador", "active_page": "admin", "users": users, "jobs": jobs, "applications": applications, "stats": stats, "job_statuses": JOB_STATUS_LABELS})


@app.post("/admin/usuarios/{id_usuario}/tipo")
def admin_update_user_type(request: Request, id_usuario: int, tipo: str = Form(...)):
    user, response = require_user(request, role="admin")
    if response:
        return response
    if tipo not in {"freelancer", "empresa", "admin"}:
        flash(request, "Tipo de usuário inválido.", "error")
        return redirect_to("/admin")
    execute_write("UPDATE Usuario SET tipo = %s WHERE id_usuario = %s", (tipo, id_usuario))
    flash(request, "Usuário atualizado.", "success")
    return redirect_to("/admin")


@app.post("/admin/usuarios/{id_usuario}/editar")
def admin_update_user(
    request: Request,
    id_usuario: int,
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(""),
    cnpj: str = Form(""),
):
    user, response = require_user(request, role="admin")
    if response:
        return response
    target = get_user_by_id(id_usuario)
    if not target:
        flash(request, "Usuário não encontrado.", "error")
        return redirect_to("/admin")
    clean_name = normalize_text(nome)
    clean_email = normalize_text(email).lower()
    clean_cpf = normalize_document(cpf)
    clean_cnpj = normalize_document(cnpj)
    if len(clean_name) < 3 or not validate_email(clean_email):
        flash(request, "Informe nome e email válidos.", "error")
        return redirect_to("/admin")
    for field, value in {"email": clean_email, "cpf": clean_cpf, "cnpj": clean_cnpj}.items():
        if value and query_one(f"SELECT id_usuario FROM Usuario WHERE {field} = %s AND id_usuario <> %s", (value, id_usuario)):
            flash(request, "Email, CPF ou CNPJ já cadastrado em outra conta.", "error")
            return redirect_to("/admin")
    execute_write(
        """
        UPDATE Usuario
        SET nome = %s, razao_social = IF(tipo = 'empresa', %s, razao_social),
            email = %s, cpf = %s, cnpj = %s
        WHERE id_usuario = %s
        """,
        (clean_name, clean_name, clean_email, clean_cpf or None, clean_cnpj or None, id_usuario),
    )
    flash(request, "Dados do usuario atualizados.", "success")
    return redirect_to("/admin")


@app.post("/admin/usuarios/{id_usuario}/excluir")
def admin_delete_user(request: Request, id_usuario: int):
    user, response = require_user(request, role="admin")
    if response:
        return response
    if user["id_usuario"] == id_usuario:
        flash(request, "O administrador logado não pode excluir a própria conta.", "error")
        return redirect_to("/admin")
    execute_write("DELETE FROM Usuario WHERE id_usuario = %s", (id_usuario,))
    flash(request, "Usuário removido.", "success")
    return redirect_to("/admin")
