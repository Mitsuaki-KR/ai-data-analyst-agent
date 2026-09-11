from src.generation.answer_synthesizer import build_synthesis_prompt, synthesize_answer


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, response_text):
        self._response_text = response_text

    def invoke(self, _prompt):
        return FakeLLMResponse(self._response_text)


def test_build_prompt_includes_question_and_data():
    prompt = build_synthesis_prompt("Quel est le CA total ?", ["total"], [(13591643.7,)])

    assert "Quel est le CA total ?" in prompt
    assert "13591643.7" in prompt


def test_build_prompt_truncates_to_20_rows():
    many_rows = [(i,) for i in range(50)]
    prompt = build_synthesis_prompt("question", ["id"], many_rows)

    assert prompt.count("(") <= 21  # 20 lignes + 1 parenthèse du template éventuel


def test_synthesize_answer_returns_stripped_llm_response():
    fake_llm = FakeLLM("  Le chiffre d'affaires total est de 13,6 millions d'euros.  ")

    result = synthesize_answer(fake_llm, "Quel est le CA total ?", ["total"], [(13591643.7,)])

    assert result == "Le chiffre d'affaires total est de 13,6 millions d'euros."