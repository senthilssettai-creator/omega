from __future__ import annotations

from pathlib import Path

from omega.agents.base import Agent
from omega.schema import MemoryKind, PluginCall, Task, TaskResult


class CodingAgent(Agent):
    name = "coding"
    system_prompt = (
        "You are OMEGA's coding agent. Inspect projects, design changes, generate files, tests, and reviews. "
        "Prefer concrete patches and verification commands."
    )

    async def run(self, task: Task) -> TaskResult:
        manifest = await self.context.plugins.call(
            PluginCall(plugin="filesystem", action="list", arguments={"path": ".", "recursive": False}),
            approved=True,
        )
        workspace_files = manifest.data if manifest.ok else []
        prompt = (
            "Create an implementation strategy for this coding task. Include files to inspect or create, "
            "test strategy, and operational risks.\n\n"
            f"Task: {task.goal}\n\nWorkspace root listing: {workspace_files}"
        )
        model_plan = await self.ask_model(task, prompt)
        if model_plan:
            summary = model_plan[:1600]
        else:
            summary = self._local_strategy(task.goal, workspace_files)
        self.context.memory.remember(
            f"Coding strategy for {task.goal}\n{summary}",
            kind=MemoryKind.PROCEDURAL,
            tags=["coding", "strategy"],
            metadata={"task_id": task.id},
            importance=0.55,
        )
        return self.result(
            task,
            summary,
            artifacts={
                "workspace_files": workspace_files,
                "model_plan": model_plan,
                "model_errors": self.model_errors,
            },
        )

    def _local_strategy(self, goal: str, workspace_files) -> str:
        file_count = len(workspace_files or [])
        package_hint = "Python package" if any(str(item.get("path", "")).endswith(".py") for item in workspace_files or []) else "new project"
        return (
            f"Local coding strategy for '{goal}': detected {file_count} top-level entries and a {package_hint}. "
            "Implement the smallest runnable slice first, add focused tests around persistent state and tool execution, "
            "then expand adapters behind clear permission checks."
        )
