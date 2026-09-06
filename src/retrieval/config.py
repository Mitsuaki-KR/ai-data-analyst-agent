from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "sql_few_shot_examples"

FEW_SHOT_EXAMPLES_PATH = PROJECT_ROOT / "data" / "few_shot_examples.json"