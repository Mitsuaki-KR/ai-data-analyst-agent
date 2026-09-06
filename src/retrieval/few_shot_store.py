import json
import logging
from pathlib import Path

import chromadb

from src.retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME
from src.retrieval.embedder import embed_texts

logger = logging.getLogger(__name__)


class RetrievalError(Exception):
    pass


def get_chroma_client(persist_dir: Path = CHROMA_DB_DIR) -> chromadb.ClientAPI:
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def load_few_shot_examples(examples_path: Path) -> list[dict]:
    if not examples_path.exists():
        raise RetrievalError(f"Fichier d'exemples introuvable : {examples_path}")

    with open(examples_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    for i, ex in enumerate(examples):
        if "question" not in ex or "sql" not in ex:
            raise RetrievalError(f"Exemple #{i} invalide, clés 'question'/'sql' requises : {ex}")

    return examples


def build_few_shot_collection(
    examples: list[dict],
    client: chromadb.ClientAPI,
    collection_name: str = COLLECTION_NAME,
) -> chromadb.Collection:
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass  # collection inexistante, rien à supprimer

    collection = client.create_collection(collection_name)

    questions = [ex["question"] for ex in examples]
    embeddings = embed_texts(questions)
    ids = [f"example_{i}" for i in range(len(examples))]
    metadatas = [{"sql": ex["sql"], "question": ex["question"]} for ex in examples]

    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=questions)

    logger.info(f"Collection '{collection_name}' construite avec {len(examples)} exemples.")
    return collection


def retrieve_similar_examples(
    question: str,
    collection: chromadb.Collection,
    k: int = 3,
) -> list[dict]:
    query_embedding = embed_texts([question])[0]

    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    return [
        {"question": m["question"], "sql": m["sql"]}
        for m in results["metadatas"][0]
    ]