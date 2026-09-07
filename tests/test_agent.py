import sqlite3

import pytest

from src.generation.agent import AgentError, SQLAgent


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """LLM factice : retourne une séquence de réponses prédéfinies,
    une par appel successif. Permet de tester la logique de retry
    sans dépendre de Groq ni du réseau."""

    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    def invoke(self, _prompt):
        return FakeLLMResponse(next(self._responses))


class FakeCollection:
    def query(self, query_embeddings, n_results):
        return {"metadatas": [[]]}  # aucun exemple few-shot pour ces tests


@pytest.fixture
def sample_db_path(tmp_path):
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, amount REAL)")
    conn.executemany("INSERT INTO orders VALUES (?, ?)", [(1, 10.0), (2, 20.0)])
    conn.commit()
    conn.close()
    return db_path


def test_agent_returns_result_on_valid_sql(sample_db_path):
    fake_llm = FakeLLM(["SELECT * FROM orders"])
    agent = SQLAgent(sample_db_path, FakeCollection(), llm_client=fake_llm)

    result = agent.ask("Combien de commandes ?")

    assert result["attempts"] == 1
    assert len(result["rows"]) == 2


def test_agent_retries_on_invalid_sql_then_succeeds(sample_db_path):
    # premier essai : requête interdite (DROP) -> rejetée par le validateur
    # deuxième essai (après retry) : requête valide
    fake_llm = FakeLLM(["DROP TABLE orders", "SELECT * FROM orders"])
    agent = SQLAgent(sample_db_path, FakeCollection(), llm_client=fake_llm, max_retries=1)

    result = agent.ask("Combien de commandes ?")

    assert result["attempts"] == 2
    assert len(result["rows"]) == 2


def test_agent_raises_after_exhausting_retries(sample_db_path):
    fake_llm = FakeLLM(["DROP TABLE orders", "DELETE FROM orders"])
    agent = SQLAgent(sample_db_path, FakeCollection(), llm_client=fake_llm, max_retries=1)

    with pytest.raises(AgentError, match="Échec après 2 tentative"):
        agent.ask("Combien de commandes ?")