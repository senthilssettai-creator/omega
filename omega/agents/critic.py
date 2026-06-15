from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import Task, TaskResult, TaskStatus


class CriticAgent(Agent):
    name = "critic"
    system_prompt = (
        "You are OMEGA's critic. Find concrete correctness, safety, verification, and completeness gaps. "
        "Report concise findings with severity and remediation."
    )

    async def run(self, task: Task) -> TaskResult:
        prompt = f"Review this goal for likely risks, missing verification, and safety controls:\n\n{task.goal}"
        model_review = await self.ask_model(task, prompt)
        summary = model_review or (
            "Critic review: verify generated artifacts compile, keep destructive actions behind approvals, "
            "confirm external integrations with credentials, and add tests for memory, permissions, plugins, and executor flow."
        )
        return self.result(
            task,
            summary,
            status=TaskStatus.SUCCEEDED,
            artifacts={"model_review": model_review, "model_errors": self.model_errors},
        )
