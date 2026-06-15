from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import PluginCall, Task, TaskResult, TaskStatus


class BrowserAgent(Agent):
    name = "browser"
    system_prompt = "You are OMEGA's browser automation agent."

    async def run(self, task: Task) -> TaskResult:
        url = task.metadata.get("url")
        if not url and self.context.online:
            search_result = await self.context.plugins.call(
                PluginCall(plugin="search", action="web", arguments={"query": task.goal, "limit": 3}),
                approved=self.context.approved,
            )
            if search_result.ok and search_result.data:
                url = search_result.data[0].get("url")
        if not url:
            return self.result(
                task,
                "Browser task identified, but no URL was supplied or discovered. Provide task metadata {'url': 'https://...'} for browser execution.",
                artifacts={"requires_url": True},
                status=TaskStatus.FAILED,
            )
        result = await self.context.plugins.call(
            PluginCall(plugin="browser", action="extract_text", arguments={"url": url}),
            approved=self.context.approved,
        )
        return self.result(task, "Browser automation completed." if result.ok else "Browser automation could not complete.", artifacts={"result": result.model_dump(mode="json")}, status=TaskStatus.SUCCEEDED if result.ok else TaskStatus.FAILED)
