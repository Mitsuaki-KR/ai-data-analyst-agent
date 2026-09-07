import sqlite3
import time


class SQLExecutionError(Exception):
    pass


def execute_readonly_query(
    conn: sqlite3.Connection,
    sql: str,
    max_rows: int,
    timeout_seconds: float,
) -> tuple[list[str], list[tuple]]:
    start = time.monotonic()

    def progress_handler():
        return 1 if (time.monotonic() - start) > timeout_seconds else 0

    conn.set_progress_handler(progress_handler, 1000)

    try:
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(max_rows)
        return columns, rows
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            raise SQLExecutionError(f"Requête interrompue : dépassement du timeout de {timeout_seconds}s")
        raise SQLExecutionError(f"Erreur SQL : {e}")
    finally:
        conn.set_progress_handler(None, 0)