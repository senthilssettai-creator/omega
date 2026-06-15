from __future__ import annotations

from dataclasses import dataclass
import logging

from omega.config import OmegaSettings
from omega.memory import MemoryStore
from omega.model_router import ModelRouter
from omega.openrouter import OpenRouterClient, OpenRouterError
from omega.plugins.registry import PluginRegistry
from omega.schema import AgentMessage, Task, TaskResult, TaskStatus


@dataclass
class AgentContext:
    settings: OmegaSettings
    memory: MemoryStore
    model_router: ModelRouter
    openrouter: OpenRouterClient
    plugins: PluginRegistry
    online: bool = False
    approved: bool = False


class Agent:
    name = "agent"
    system_prompt = "You are an autonomous OMEGA subsystem."

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.model_errors: list[str] = []
        self.logger = logging.getLogger(f"omega.agent.{self.name}")

    async def run(self, task: Task) -> TaskResult:
        raise NotImplementedError

    def result(self, task: Task, summary: str, *, status: TaskStatus = TaskStatus.SUCCEEDED, artifacts=None, messages=None) -> TaskResult:
        return TaskResult(
            task_id=task.id,
            agent=self.name,
            status=status,
            summary=summary,
            artifacts=artifacts or {},
            messages=messages or [],
        )

    async def ask_model(self, task: Task, prompt: str, *, max_tokens: int = 1600) -> str | None:
        self.model_errors = []
        if not self.context.openrouter.available():
            return None
        messages = [
            AgentMessage(role="system", content=self.system_prompt),
            AgentMessage(role="user", content=prompt),
        ]
        for model in self.context.model_router.candidates(task.task_type):
            try:
                return await self.context.openrouter.chat(model=model, messages=messages, max_tokens=max_tokens)
            except OpenRouterError as exc:
                message = f"{model}: {exc}"
                self.model_errors.append(message)
                self.logger.warning(message, extra={"event": "model_fallback"})
        return None
