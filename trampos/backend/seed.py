from pathlib import Path

import pymysql

from app.database import get_connection, get_database_name

SQL_FILE = Path(__file__).with_name("trampos.sql")


def iter_statements(sql_script: str):
    cleaned_lines: list[str] = []
    for raw_line in sql_script.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith("--"):
            continue

        line_without_inline_comment = raw_line.split("--", 1)[0].rstrip()
        if line_without_inline_comment:
            cleaned_lines.append(line_without_inline_comment)

    for statement in "\n".join(cleaned_lines).split(";"):
        normalized = statement.strip()
        if normalized:
            yield normalized


def main() -> None:
    database_name = get_database_name()
    if not database_name:
        raise RuntimeError("Defina o nome do banco em DATABASE_URL antes de executar o seed.")

    sql_script = SQL_FILE.read_text(encoding="utf-8")
    connection = get_connection(cursorclass=pymysql.cursors.Cursor, database=None)

    try:
        with connection.cursor() as cursor:
            for statement in iter_statements(sql_script):
                cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print("✅ Banco recriado com os dados de exemplo do arquivo trampos.sql.")
    print(f"Banco: {database_name}")
    print("Login empresa: tech@trampos.dev / senha123")
    print("Login freelancer: ana@trampos.dev / senha123")


if __name__ == "__main__":
    main()
