import os
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

import pymysql
from dotenv import load_dotenv
from fastapi import HTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost/trampos"
)

_schema_checked = False
_schema_lock = Lock()


def parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        raise RuntimeError("DATABASE_URL deve usar mysql+pymysql://")

    return {
        "host": parsed.hostname or "localhost",
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "db": (parsed.path or "").lstrip("/") or "trampos",
        "port": parsed.port or 3306,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }


def ensure_schema(conn) -> None:
    global _schema_checked

    if _schema_checked:
        return

    with _schema_lock:
        if _schema_checked:
            return

        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'Usuario'
                  AND COLUMN_NAME = 'avatar_url'
                '''
            )
            if not cur.fetchone():
                cur.execute(
                    '''
                    ALTER TABLE Usuario
                    ADD COLUMN avatar_url VARCHAR(255) NULL AFTER tipo
                    '''
                )
                conn.commit()

        _schema_checked = True


def get_db():
    params = parse_database_url(DATABASE_URL)
    try:
        conn = pymysql.connect(**params)
        ensure_schema(conn)
    except pymysql.MySQLError as exc:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados indisponivel. Inicie o MySQL e confira a DATABASE_URL.",
        ) from exc
    try:
        yield conn
    finally:
        conn.close()
