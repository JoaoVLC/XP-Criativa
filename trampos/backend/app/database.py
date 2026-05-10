import os
from urllib.parse import unquote, urlparse

import pymysql
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost/trampos"
)
SESSION_SECRET = os.getenv("SESSION_SECRET", "trampos")

_DEFAULT_DATABASE = object()


def parse_database_url(url: str = DATABASE_URL) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError("DATABASE_URL deve usar o esquema mysql+pymysql://")

    database = parsed.path.lstrip("/") or None
    return {
        "host": parsed.hostname or "localhost",
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "port": parsed.port or 3306,
        "database": database,
        "charset": "utf8mb4",
        "autocommit": False,
    }


def get_database_name() -> str | None:
    return parse_database_url().get("database")


def get_connection(
    *,
    cursorclass=pymysql.cursors.DictCursor,
    database=_DEFAULT_DATABASE,
):
    config = parse_database_url()
    config["cursorclass"] = cursorclass

    if database is not _DEFAULT_DATABASE:
        if database is None:
            config.pop("database", None)
        else:
            config["database"] = database

    return pymysql.connect(**config)
