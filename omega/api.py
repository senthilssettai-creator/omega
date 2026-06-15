from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from omega.runtime import OmegaRuntime


class GoalRequest(BaseModel):
    goal: str
    online: bool = False
    approved: bool = False


class PluginRequest(BaseModel):
    plugin: str
    action: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False


@lru_cache(maxsize=1)
def runtime() -> OmegaRuntime:
    return OmegaRuntime.create()


app = FastAPI(title="OMEGA API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/plugins")
async def plugins() -> dict[str, Any]:
    return runtime().plugins.manifest()


@app.post("/goals")
async def execute_goal(request: GoalRequest) -> dict[str, Any]:
    rt = OmegaRuntime.create(online=request.online, approved=request.approved)
    try:
        return await rt.execute_goal(request.goal)
    finally:
        rt.close()


@app.post("/plugins/call")
async def call_plugin(request: PluginRequest) -> dict[str, Any]:
    result = await runtime().call_plugin(request.plugin, request.action, request.arguments, approved=request.approved)
    return result.model_dump(mode="json")


@app.get("/memory/search")
async def memory_search(query: str, limit: int = 10) -> dict[str, Any]:
    results = runtime().memory.search(query, limit=limit)
    return {"results": [{"record": record.model_dump(mode="json"), "score": score} for record, score in results]}
