import sqlite3


def get_schema_description(conn: sqlite3.Connection) -> str:
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    lines = []
    for (table_name,) in tables:
        columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        column_names = ", ".join(col[1] for col in columns)
        lines.append(f"{table_name}({column_names})")

    return "\n".join(lines)