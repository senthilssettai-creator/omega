from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import PluginCall, Task, TaskResult


class DevOpsAgent(Agent):
    name = "devops"
    system_prompt = "You are OMEGA's DevOps agent for Git, Docker, CI, deployment, and infrastructure checks."

    async def run(self, task: Task) -> TaskResult:
        status = await self.context.plugins.call(PluginCall(plugin="git", action="status", arguments={}), approved=True)
        docker = await self.context.plugins.call(PluginCall(plugin="docker", action="ps", arguments={}), approved=True)
        summary = "Collected repository and Docker operational context."
        artifacts = {
            "git_status": status.model_dump(mode="json"),
            "docker_ps": docker.model_dump(mode="json"),
        }
        return self.result(task, summary, artifacts=artifacts)
