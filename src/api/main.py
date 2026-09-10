import base64

from fastapi import Depends, FastAPI, HTTPException

from src.api.dependencies import get_agent
from src.api.schemas import AskRequest, AskResponse
from src.generation.agent import AgentError, SQLAgent
from src.viz.chart_generator import generate_chart
from src.viz.chart_selector import select_chart_type

app = FastAPI(title="AI Data Analyst Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, agent: SQLAgent = Depends(get_agent)):
    try:
        result = agent.ask(request.question)
    except AgentError as e:
        raise HTTPException(status_code=422, detail=str(e))

    chart_type = select_chart_type(result["columns"], result["rows"])
    chart_base64 = None
    if chart_type:
        chart_bytes = generate_chart(result["columns"], result["rows"], chart_type, request.question)
        chart_base64 = base64.b64encode(chart_bytes).decode("utf-8")

    return AskResponse(
        sql=result["sql"],
        columns=result["columns"],
        rows=result["rows"],
        chart_base64=chart_base64,
    )