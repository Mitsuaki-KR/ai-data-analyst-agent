from evaluation.run_eval import rows_to_csv, summarize


def test_rows_to_csv_includes_header_and_rows():
    csv_text = rows_to_csv(["id", "amount"], [(1, 10.5), (2, 20.0)])

    lines = csv_text.strip().splitlines()
    assert lines[0] == "id,amount"
    assert lines[1] == "1,10.5"
    assert lines[2] == "2,20.0"


def test_summarize_computes_correct_averages():
    results = [
        {"execution_success": True, "datacompy_f1": 1.0, "semantic_equivalence": 1.0},
        {"execution_success": True, "datacompy_f1": 0.0, "semantic_equivalence": 0.0},
        {"execution_success": False},
    ]

    summary = summarize(results)

    assert summary["total_questions"] == 3
    assert summary["execution_success_rate"] == 2 / 3
    assert summary["avg_datacompy_f1"] == 0.5
    assert summary["semantic_equivalence_rate"] == 0.5


def test_summarize_handles_all_failures():
    results = [{"execution_success": False}, {"execution_success": False}]

    summary = summarize(results)

    assert summary["execution_success_rate"] == 0
    assert summary["avg_datacompy_f1"] is None
    assert summary["semantic_equivalence_rate"] is None