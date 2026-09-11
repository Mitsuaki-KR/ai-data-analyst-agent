from fastapi.testclient import TestClient

from src.api.dependencies import get_agent
from src.api.main import app
from src.generation.agent import AgentError

PNG_SIGNATURE_B64_PREFIX = "iVBORw0KGgo"  # signature PNG encodée en base64

client = TestClient(app)


class FakeLLM:
    def invoke(self, _prompt):
        class Response:
            content = "Réponse de test générée."
        return Response()


class FakeAgent:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error
        self.llm = FakeLLM()

    def ask(self, question):
        if self._error:
            raise self._error
        return self._result


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_no_chart_for_single_value_result():
    fake_result = {
        "sql": "SELECT SUM(price) AS total FROM order_items",
        "columns": ["total"],
        "rows": [(13591643.7,)],
        "attempts": 1,
    }
    app.dependency_overrides[get_agent] = lambda: FakeAgent(result=fake_result)

    response = client.post("/ask", json={"question": "Quel est le CA total ?"})

    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == fake_result["sql"]
    assert data["chart_base64"] is None
    assert data["answer"] == "Réponse de test générée."

    app.dependency_overrides.clear()


def test_ask_returns_chart_for_multi_row_result():
    fake_result = {
        "sql": "SELECT product_id, COUNT(*) AS quantity FROM order_items GROUP BY product_id",
        "columns": ["product_id", "quantity"],
        "rows": [("p1", 10), ("p2", 5)],
        "attempts": 1,
    }
    app.dependency_overrides[get_agent] = lambda: FakeAgent(result=fake_result)

    response = client.post("/ask", json={"question": "top produits"})

    assert response.status_code == 200
    data = response.json()
    assert data["chart_base64"] is not None
    assert data["chart_base64"].startswith(PNG_SIGNATURE_B64_PREFIX)
    assert data["answer"] == "Réponse de test générée."
    app.dependency_overrides.clear()


def test_ask_returns_422_when_agent_fails():
    app.dependency_overrides[get_agent] = lambda: FakeAgent(error=AgentError("échec après 3 tentatives"))

    response = client.post("/ask", json={"question": "question impossible à traduire"})

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_ask_rejects_empty_question():
    response = client.post("/ask", json={"question": ""})

    assert response.status_code == 422