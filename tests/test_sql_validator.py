import pytest

from src.generation.sql_validator import SQLValidationError, validate_readonly_sql


def test_valid_select_passes():
    result = validate_readonly_sql("SELECT * FROM orders")
    assert result == "SELECT * FROM orders"


def test_valid_with_cte_passes():
    result = validate_readonly_sql("WITH t AS (SELECT 1) SELECT * FROM t")
    assert "WITH" in result


def test_insert_is_rejected():
    with pytest.raises(SQLValidationError, match="SELECT/WITH"):
        validate_readonly_sql("INSERT INTO orders VALUES (1)")


def test_delete_is_rejected():
    with pytest.raises(SQLValidationError, match="SELECT/WITH"):
        validate_readonly_sql("DELETE FROM orders")


def test_drop_table_is_rejected():
    with pytest.raises(SQLValidationError, match="SELECT/WITH"):
        validate_readonly_sql("DROP TABLE orders")


def test_forbidden_keyword_inside_select_is_rejected():
    # une seule instruction (pas de ';'), pour isoler précisément
    # la vérification des mots-clés interdits, indépendamment
    # de la vérification anti-injection multi-requêtes
    with pytest.raises(SQLValidationError, match="interdits"):
        validate_readonly_sql("WITH x AS (DELETE FROM orders) SELECT * FROM x")

def test_column_named_like_forbidden_keyword_is_not_falsely_rejected():
    # 'is_deleted' contient 'DELETE' en sous-chaîne mais n'est pas le mot-clé DELETE
    result = validate_readonly_sql("SELECT is_deleted FROM orders")
    assert result == "SELECT is_deleted FROM orders"


def test_multiple_statements_rejected():
    with pytest.raises(SQLValidationError, match="Plusieurs instructions"):
        validate_readonly_sql("SELECT 1; SELECT 2")