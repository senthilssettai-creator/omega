from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import PluginCall, Task, TaskResult, TaskStatus


class TerminalAgent(Agent):
    name = "terminal"
    system_prompt = (
        "You are OMEGA's terminal agent. Translate user goals into safe shell actions and only use the terminal plugin when the task explicitly requires it. "
        "When possible, split goals into precise, non-destructive commands and include the expected outcome in the report."
    )

    async def run(self, task: Task) -> TaskResult:
        if not task.metadata.get("command"):
            return self.result(
                task,
                "Terminal task identified, but no command metadata was provided. Supply task metadata {'command': '...'} to execute.",
                artifacts={"requires_command": True},
                status=TaskStatus.FAILED,
            )

        result = await self.context.plugins.call(
            PluginCall(plugin="terminal", action="run", arguments={"command": task.metadata["command"]}),
            approved=self.context.approved,
        )
        status = TaskStatus.SUCCEEDED if result.ok else TaskStatus.FAILED
        summary = f"Terminal command executed: {task.metadata['command']}"
        if not result.ok:
            summary += f"; error: {result.error or 'unknown'}"
        return self.result(task, summary, status=status, artifacts={"result": result.model_dump(mode="json")})
