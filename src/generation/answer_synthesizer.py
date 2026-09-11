from groq import RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

SYNTHESIS_TEMPLATE = """Tu es un analyste de données qui explique un résultat en langage naturel, de façon claire et concise.

Question posée : {question}

Données obtenues (colonnes : {columns}) :
{rows}

Réponds en 1 à 3 phrases, dans la même langue que la question, en te basant uniquement sur ces données. Ne mentionne jamais le SQL ni les noms de colonnes techniques."""


def build_synthesis_prompt(question: str, columns: list[str], rows: list[tuple]) -> str:
    rows_text = "\n".join(str(row) for row in rows[:20])
    return SYNTHESIS_TEMPLATE.format(question=question, columns=columns, rows=rows_text)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
)
def synthesize_answer(llm_client, question: str, columns: list[str], rows: list[tuple]) -> str:
    prompt = build_synthesis_prompt(question, columns, rows)
    response = llm_client.invoke(prompt)
    return response.content.strip()