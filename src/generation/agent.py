import sqlite3

from langchain_groq import ChatGroq

from src.generation.config import GROQ_API_KEY, MAX_RETRIES, MAX_ROWS_RETURNED, MODEL_NAME, QUERY_TIMEOUT_SECONDS
from src.generation.prompts import build_generation_prompt, build_retry_prompt, extract_sql_from_response
from src.generation.schema_utils import get_schema_description
from src.generation.sql_executor import SQLExecutionError, execute_readonly_query
from src.generation.sql_validator import SQLValidationError, validate_readonly_sql
from src.retrieval.few_shot_store import retrieve_similar_examples


class AgentError(Exception):
    pass


class SQLAgent:
    def __init__(self, db_path, chroma_collection, llm_client=None, max_retries: int = MAX_RETRIES):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.collection = chroma_collection
        self.llm = llm_client or ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY, temperature=0)
        self.max_retries = max_retries
        self.schema = get_schema_description(self.conn)

    def ask(self, question: str) -> dict:
        examples = retrieve_similar_examples(question, self.collection, k=3)
        prompt = build_generation_prompt(self.schema, examples, question)
        sql = self._generate_sql(prompt)

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                validated_sql = validate_readonly_sql(sql)
                columns, rows = execute_readonly_query(
                    self.conn, validated_sql, MAX_ROWS_RETURNED, QUERY_TIMEOUT_SECONDS
                )
                return {"sql": validated_sql, "columns": columns, "rows": rows, "attempts": attempt + 1}
            except (SQLValidationError, SQLExecutionError) as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    retry_prompt = build_retry_prompt(self.schema, question, sql, last_error)
                    sql = self._generate_sql(retry_prompt)

        raise AgentError(f"Échec après {self.max_retries + 1} tentative(s). Dernière erreur : {last_error}")

    def _generate_sql(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return extract_sql_from_response(response.content)