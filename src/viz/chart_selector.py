def select_chart_type(columns: list[str], rows: list[tuple]) -> str | None:
    if len(rows) < 2:
        return None

    if len(columns) != 2:
        return None

    if not all(isinstance(row[1], (int, float)) for row in rows):
        return None

    temporal_keywords = ("date", "month", "year", "week", "day")
    label_column = columns[0].lower()

    if any(keyword in label_column for keyword in temporal_keywords):
        return "line"

    return "bar"