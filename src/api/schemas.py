from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    sql: str
    columns: list[str]
    rows: list[tuple]
    chart_base64: str | None = None