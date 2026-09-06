from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.retrieval.config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    # cache le modèle en mémoire, évite un rechargement disque à chaque appel
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vectors = model.encode(texts, convert_to_numpy=True)
    return vectors.tolist()