import sys
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.config import DB_PATH
from src.retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME, FEW_SHOT_EXAMPLES_PATH
from src.retrieval.few_shot_store import build_few_shot_collection, get_chroma_client, load_few_shot_examples
from src.generation.agent import SQLAgent

# construit (ou reconstruit) la collection ChromaDB à partir des exemples
client = get_chroma_client(CHROMA_DB_DIR)
examples = load_few_shot_examples(FEW_SHOT_EXAMPLES_PATH)
collection = build_few_shot_collection(examples, client, COLLECTION_NAME)

agent = SQLAgent(DB_PATH, collection)

questions = [
    "Quel est le chiffre d'affaires total ?",
    "Quels sont les 5 produits les plus vendus ?",
    "Quel est le délai de livraison moyen en jours ?",
]

for question in questions:
    print(f"\n{'='*60}")
    print(f"Question : {question}")
    try:
        result = agent.ask(question)
        print(f"SQL généré : {result['sql']}")
        print(f"Colonnes   : {result['columns']}")
        print(f"Résultat   : {result['rows'][:5]}")
        print(f"Tentatives : {result['attempts']}")
    except Exception as e:
        print(f"ÉCHEC : {e}")