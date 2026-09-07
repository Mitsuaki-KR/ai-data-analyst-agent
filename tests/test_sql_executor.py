import sqlite3

import pytest

from src.generation.sql_executor import SQLExecutionError, execute_readonly_query


@pytest.fixture
def sample_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, amount REAL)")
    conn.executemany("INSERT INTO orders VALUES (?, ?)", [(1, 10.0), (2, 20.0), (3, 30.0)])
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def bigger_db(tmp_path):
    # jeu de données plus volumineux, dédié au test de timeout :
    # il faut assez de lignes pour que la requête dure "vraiment" un peu,
    # sinon SQLite finit avant même le premier appel du progress handler
    db_path = tmp_path / "test_big.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, amount REAL)")
    conn.executemany("INSERT INTO orders VALUES (?, ?)", [(i, float(i)) for i in range(50)])
    conn.commit()
    yield conn
    conn.close()


def test_execute_returns_correct_columns_and_rows(sample_db):
    columns, rows = execute_readonly_query(sample_db, "SELECT id, amount FROM orders", max_rows=10, timeout_seconds=5)

    assert columns == ["id", "amount"]
    assert len(rows) == 3


def test_max_rows_limits_result_size(sample_db):
    columns, rows = execute_readonly_query(sample_db, "SELECT * FROM orders", max_rows=2, timeout_seconds=5)

    assert len(rows) == 2


def test_invalid_sql_raises_clear_error(sample_db):
    with pytest.raises(SQLExecutionError, match="Erreur SQL"):
        execute_readonly_query(sample_db, "SELECT * FROM table_inexistante", max_rows=10, timeout_seconds=5)


def test_slow_query_is_interrupted_by_timeout(bigger_db):
    # 50^5 = ~312 millions de lignes générées : largement de quoi dépasser
    # un timeout de quelques millisecondes avant la fin naturelle de la requête
    slow_sql = """
        SELECT COUNT(*) FROM orders a, orders b, orders c, orders d, orders e
    """
    with pytest.raises(SQLExecutionError, match="timeout"):
        execute_readonly_query(bigger_db, slow_sql, max_rows=10, timeout_seconds=0.01)