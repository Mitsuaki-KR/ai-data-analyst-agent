import json

import pytest

from src.retrieval.few_shot_store import (
    RetrievalError,
    build_few_shot_collection,
    get_chroma_client,
    load_few_shot_examples,
    retrieve_similar_examples,
)


@pytest.fixture
def tiny_examples():
    return [
        {"question": "Quel est le chiffre d'affaires total ?", "sql": "SELECT SUM(price) FROM order_items"},
        {"question": "Quelle est la note moyenne des avis ?", "sql": "SELECT AVG(review_score) FROM order_reviews"},
        {"question": "Combien de vendeurs distincts existe-t-il ?", "sql": "SELECT COUNT(DISTINCT seller_id) FROM sellers"},
    ]


def test_load_few_shot_examples_valid(tmp_path):
    examples_path = tmp_path / "examples.json"
    examples_path.write_text(json.dumps([{"question": "Q1", "sql": "SELECT 1"}]), encoding="utf-8")

    examples = load_few_shot_examples(examples_path)

    assert examples == [{"question": "Q1", "sql": "SELECT 1"}]


def test_load_few_shot_examples_missing_file_raises(tmp_path):
    with pytest.raises(RetrievalError, match="introuvable"):
        load_few_shot_examples(tmp_path / "does_not_exist.json")


def test_load_few_shot_examples_invalid_entry_raises(tmp_path):
    examples_path = tmp_path / "examples.json"
    examples_path.write_text(json.dumps([{"question": "Q1"}]), encoding="utf-8")

    with pytest.raises(RetrievalError, match="invalide"):
        load_few_shot_examples(examples_path)


def test_retrieve_returns_most_semantically_similar_example(tmp_path, tiny_examples):
    client = get_chroma_client(persist_dir=tmp_path / "chroma_test")
    collection = build_few_shot_collection(tiny_examples, client)

    results = retrieve_similar_examples(
        "Comment les clients évaluent-ils leurs achats en général ?",
        collection,
        k=1,
    )

    assert len(results) == 1
    assert "review_score" in results[0]["sql"]


def test_retrieve_respects_k_limit(tmp_path, tiny_examples):
    client = get_chroma_client(persist_dir=tmp_path / "chroma_test_k")
    collection = build_few_shot_collection(tiny_examples, client)

    results = retrieve_similar_examples("Question quelconque", collection, k=2)

    assert len(results) == 2


def test_build_collection_is_idempotent(tmp_path, tiny_examples):
    client = get_chroma_client(persist_dir=tmp_path / "chroma_test_idempotent")
    build_few_shot_collection(tiny_examples, client)
    collection = build_few_shot_collection(tiny_examples, client)

    assert collection.count() == len(tiny_examples)