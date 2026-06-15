from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import PluginCall, Task, TaskResult, TaskStatus


class ResearchAgent(Agent):
    name = "research"
    system_prompt = (
        "You are OMEGA's research agent. Summarize sources, compare findings, and produce concise reports. "
        "Use explicit rationale summaries and cite retrieved source URLs when available."
    )

    async def run(self, task: Task) -> TaskResult:
        artifacts = {"sources": [], "model_report": None, "model_errors": []}
        if self.context.online:
            result = await self.context.plugins.call(
                PluginCall(plugin="search", action="web", arguments={"query": task.goal, "limit": 5}),
                approved=self.context.approved,
            )
            if result.ok:
                artifacts["sources"] = result.data
        prompt = (
            "Research this goal and produce a compact report with: relevant context, risks, "
            f"implementation implications, and next checks.\n\nGoal: {task.goal}\n\nSources: {artifacts['sources']}"
        )
        model_report = await self.ask_model(task, prompt)
        artifacts["model_errors"] = self.model_errors
        if model_report:
            artifacts["model_report"] = model_report
            summary = model_report[:1200]
        elif artifacts["sources"]:
            summary = "Collected web search sources for the goal. Review source snippets before acting."
        else:
            summary = "No live research was run. Enable online mode or configure OpenRouter for deeper research."
        return self.result(task, summary, status=TaskStatus.SUCCEEDED, artifacts=artifacts)
