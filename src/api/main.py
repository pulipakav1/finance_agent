"""FastAPI entrypoint for the financial intelligence platform."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.fin_platform.config import settings
from src.fin_platform.graph import FinancialIntelligenceGraph
from src.fin_platform.observability import logger, setup_logging

platform_graph: FinancialIntelligenceGraph | None = None


class QueryRequest(BaseModel):
    query: str
    thread_id: str = Field(default="default-thread")
    session_metadata: dict[str, Any] = Field(default_factory=dict)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global platform_graph
    setup_logging()
    logger.info("booting_platform app=%s env=%s", settings.app_name, settings.env)
    platform_graph = FinancialIntelligenceGraph()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Production-style multi-agent financial intelligence API.",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "graph_ready": platform_graph is not None, "data_mode": settings.data_mode}


@app.post("/query")
def query(request: QueryRequest) -> dict[str, Any]:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if platform_graph is None:
        raise HTTPException(status_code=503, detail="Platform not initialized")
    try:
        return platform_graph.invoke(
            query=request.query,
            thread_id=request.thread_id,
            session_metadata=request.session_metadata,
            conversation_history=request.conversation_history,
        )
    except Exception as exc:
        logger.exception("query_failed thread_id=%s err=%s", request.thread_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
