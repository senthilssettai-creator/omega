from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import MemoryKind, Task, TaskResult


class MemoryAgent(Agent):
    name = "memory"
    system_prompt = "You manage OMEGA's persistent semantic, episodic, procedural, and user memories."

    async def run(self, task: Task) -> TaskResult:
        query = task.goal
        matches = self.context.memory.search(query, limit=8)
        record = self.context.memory.remember(
            f"Active goal context: {query}",
            kind=MemoryKind.SHORT_TERM,
            tags=["active-goal"],
            metadata={"task_id": task.id},
            importance=0.4,
        )
        summary = "Stored active goal context and recalled relevant memories."
        artifacts = {
            "stored": record.model_dump(mode="json"),
            "matches": [{"record": item.model_dump(mode="json"), "score": score} for item, score in matches],
        }
        return self.result(task, summary, artifacts=artifacts)
