from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from omega.runtime import OmegaRuntime


class WorkflowStep(BaseModel):
    name: str
    type: str = "goal"
    goal: str | None = None
    plugin: str | None = None
    action: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False


class Workflow(BaseModel):
    name: str
    description: str = ""
    schedule: str | None = None
    steps: list[WorkflowStep]


def load_workflow(path: Path) -> Workflow:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to load YAML workflows.") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return Workflow.model_validate(data)


async def run_workflow(runtime: OmegaRuntime, workflow: Workflow) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for step in workflow.steps:
        if step.type == "goal":
            if not step.goal:
                raise ValueError(f"Workflow step '{step.name}' is missing goal.")
            result = await runtime.execute_goal(step.goal)
            results.append({"step": step.name, "type": step.type, "result": result})
        elif step.type == "plugin":
            if not step.plugin or not step.action:
                raise ValueError(f"Workflow step '{step.name}' is missing plugin/action.")
            result = await runtime.call_plugin(step.plugin, step.action, step.arguments, approved=step.approved)
            results.append({"step": step.name, "type": step.type, "result": result.model_dump(mode="json")})
        else:
            raise ValueError(f"Unsupported workflow step type: {step.type}")
        await asyncio.sleep(0)
    return {"workflow": workflow.name, "results": results}
