from src.viz.chart_selector import select_chart_type


def test_no_rows_returns_none():
    assert select_chart_type(["total"], []) is None


def test_single_row_returns_none():
    # une valeur agrégée unique (ex: SUM, COUNT) n'a pas besoin de graphique
    assert select_chart_type(["total_revenue"], [(13591643.7,)]) is None


def test_more_than_two_columns_returns_none():
    columns = ["product_id", "quantity", "revenue"]
    rows = [("p1", 10, 100.0), ("p2", 5, 50.0)]
    assert select_chart_type(columns, rows) is None


def test_non_numeric_second_column_returns_none():
    columns = ["product_id", "category_name"]
    rows = [("p1", "electronics"), ("p2", "books")]
    assert select_chart_type(columns, rows) is None


def test_categorical_data_returns_bar():
    columns = ["product_id", "quantity"]
    rows = [("p1", 10), ("p2", 5)]
    assert select_chart_type(columns, rows) == "bar"


def test_temporal_column_name_returns_line():
    columns = ["month", "order_count"]
    rows = [("2017-01", 100), ("2017-02", 120)]
    assert select_chart_type(columns, rows) == "line"