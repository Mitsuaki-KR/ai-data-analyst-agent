import asyncio
import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from openai import RateLimitError as OpenAIRateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from openai import AsyncOpenAI
from ragas.llms.base import llm_factory
from ragas.metrics.collections import DataCompyScore, SQLSemanticEquivalence

from src.generation.agent import AgentError, SQLAgent
from src.generation.config import GROQ_API_KEY, MODEL_NAME
from src.generation.schema_utils import get_schema_description
from src.ingestion.config import DB_PATH
from src.retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME, FEW_SHOT_EXAMPLES_PATH
from src.retrieval.few_shot_store import build_few_shot_collection, get_chroma_client, load_few_shot_examples

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTSET_PATH = PROJECT_ROOT / "evaluation" / "testset.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"


def rows_to_csv(columns: list[str], rows: list[tuple]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    writer.writerows(rows)
    return buffer.getvalue()


def summarize(results: list[dict]) -> dict:
    total = len(results)
    executed = [r for r in results if r["execution_success"]]

    datacompy_scores = [r["datacompy_f1"] for r in executed if "datacompy_f1" in r]
    equivalence_scores = [r["semantic_equivalence"] for r in executed if "semantic_equivalence" in r]

    return {
        "total_questions": total,
        "execution_success_rate": len(executed) / total if total else 0,
        "avg_datacompy_f1": sum(datacompy_scores) / len(datacompy_scores) if datacompy_scores else None,
        "semantic_equivalence_rate": sum(equivalence_scores) / len(equivalence_scores) if equivalence_scores else None,
    }


def build_evaluator_llm():
    client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    return llm_factory(MODEL_NAME, provider="openai", client=client)


@retry(
    retry=retry_if_exception_type(OpenAIRateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
)
async def evaluate_single(agent, conn, schema_contexts, evaluator_llm, item):
    question = item["question"]
    reference_sql = item["reference_sql"]
    entry = {"question": question, "reference_sql": reference_sql}

    try:
        agent_result = agent.ask(question)
    except AgentError as e:
        entry.update({"generated_sql": None, "execution_success": False, "error": str(e)})
        return entry

    entry["generated_sql"] = agent_result["sql"]
    entry["execution_success"] = True
    entry["attempts"] = agent_result["attempts"]

    ref_cursor = conn.execute(reference_sql)
    ref_columns = [d[0] for d in ref_cursor.description]
    ref_rows = ref_cursor.fetchall()

    generated_csv = rows_to_csv(agent_result["columns"], agent_result["rows"])
    reference_csv = rows_to_csv(ref_columns, ref_rows)

    datacompy_result = await DataCompyScore().ascore(response=generated_csv, reference=reference_csv)
    entry["datacompy_f1"] = datacompy_result.value

    equivalence_result = await SQLSemanticEquivalence(llm=evaluator_llm).ascore(
        response=agent_result["sql"],
        reference=reference_sql,
        reference_contexts=schema_contexts,
    )
    entry["semantic_equivalence"] = equivalence_result.value
    entry["semantic_equivalence_reason"] = equivalence_result.reason

    return entry


async def run_evaluation() -> list[dict]:
    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))

    chroma_client = get_chroma_client(CHROMA_DB_DIR)
    examples = load_few_shot_examples(FEW_SHOT_EXAMPLES_PATH)
    collection = build_few_shot_collection(examples, chroma_client, COLLECTION_NAME)
    agent = SQLAgent(DB_PATH, collection)

    conn = sqlite3.connect(DB_PATH)
    schema_contexts = get_schema_description(conn).split("\n")
    evaluator_llm = build_evaluator_llm()

    results = []
    for item in testset:
        entry = await evaluate_single(agent, conn, schema_contexts, evaluator_llm, item)
        results.append(entry)
        print(f"[{'OK' if entry['execution_success'] else 'FAIL'}] {entry['question']}")

    conn.close()
    return results


def save_report(results: list[dict], summary: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"eval_{timestamp}.json"
    report_path.write_text(
        json.dumps({"summary": summary, "details": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report_path


if __name__ == "__main__":
    results = asyncio.run(run_evaluation())
    summary = summarize(results)

    print("\n" + "=" * 50)
    print("RÉSUMÉ DE L'ÉVALUATION")
    print("=" * 50)
    print(f"Questions testées              : {summary['total_questions']}")
    print(f"Taux d'exécution réussie       : {summary['execution_success_rate']:.1%}")
    if summary["avg_datacompy_f1"] is not None:
        print(f"Score DataCompy moyen (F1)     : {summary['avg_datacompy_f1']:.3f}")
    if summary["semantic_equivalence_rate"] is not None:
        print(f"Taux d'équivalence sémantique  : {summary['semantic_equivalence_rate']:.1%}")

    report_path = save_report(results, summary)
    print(f"\nRapport complet : {report_path}")