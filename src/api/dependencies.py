from functools import lru_cache

from src.generation.agent import SQLAgent
from src.ingestion.config import DB_PATH
from src.retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME, FEW_SHOT_EXAMPLES_PATH
from src.retrieval.few_shot_store import build_few_shot_collection, get_chroma_client, load_few_shot_examples


@lru_cache(maxsize=1)
def get_agent() -> SQLAgent:
    client = get_chroma_client(CHROMA_DB_DIR)
    examples = load_few_shot_examples(FEW_SHOT_EXAMPLES_PATH)
    collection = build_few_shot_collection(examples, client, COLLECTION_NAME)
    return SQLAgent(DB_PATH, collection)