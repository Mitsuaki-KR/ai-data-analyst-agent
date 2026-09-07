SQL_GENERATION_TEMPLATE = """Tu es un expert SQL qui traduit des questions en langage naturel en requêtes SQLite.

Schéma de la base de données :
{schema}

Exemples de questions similaires et leurs requêtes SQL correctes :
{examples}

Règles strictes :
- Réponds uniquement avec la requête SQL, sans explication, sans texte autour.
- Utilise uniquement SELECT ou WITH, jamais d'instruction de modification.
- N'utilise que les tables et colonnes listées dans le schéma ci-dessus.

Question : {question}

Requête SQL :"""

RETRY_TEMPLATE = """La requête SQL précédente a échoué.

Schéma de la base de données :
{schema}

Question originale : {question}

Requête précédente : {previous_sql}

Erreur obtenue : {error}

Corrige la requête pour qu'elle soit valide et réponde à la question.
Réponds uniquement avec la requête SQL corrigée, sans explication."""


def build_generation_prompt(schema: str, examples: list[dict], question: str) -> str:
    examples_text = "\n".join(
        f"Q: {ex['question']}\nSQL: {ex['sql']}" for ex in examples
    )
    return SQL_GENERATION_TEMPLATE.format(schema=schema, examples=examples_text, question=question)


def build_retry_prompt(schema: str, question: str, previous_sql: str, error: str) -> str:
    return RETRY_TEMPLATE.format(schema=schema, question=question, previous_sql=previous_sql, error=error)


def extract_sql_from_response(raw_text: str) -> str:
    text = raw_text.strip()
    if "```" in text:
        text = text.split("```")[1]
        text = text.removeprefix("sql").strip()
    return text.strip()