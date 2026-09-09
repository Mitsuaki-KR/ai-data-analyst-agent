from src.viz.chart_generator import generate_chart

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_generates_valid_png_bytes():
    columns = ["product_id", "quantity"]
    rows = [("p1", 10), ("p2", 5)]

    result = generate_chart(columns, rows, "bar", "Top produits")

    assert result.startswith(PNG_SIGNATURE)


def test_line_chart_generates_valid_png():
    columns = ["month", "order_count"]
    rows = [("2017-01", 100), ("2017-02", 120)]

    result = generate_chart(columns, rows, "line", "Commandes par mois")

    assert result.startswith(PNG_SIGNATURE)


def test_invalid_chart_type_raises():
    import pytest

    with pytest.raises(ValueError, match="non supporté"):
        generate_chart(["a", "b"], [("x", 1)], "pie", "Titre")


def test_handles_special_characters_in_labels():
    # les catégories Olist contiennent des caractères portugais (accents),
    # doit fonctionner sans crash d'encodage
    columns = ["categoria", "quantity"]
    rows = [("eletrônicos", 50), ("móveis", 30)]

    result = generate_chart(columns, rows, "bar", "Catégories")

    assert result.startswith(PNG_SIGNATURE)