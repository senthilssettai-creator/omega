from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from omega.agents.base import AgentContext
from omega.agents.browser_agent import BrowserAgent
from omega.agents.coding import CodingAgent
from omega.agents.critic import CriticAgent
from omega.agents.devops import DevOpsAgent
from omega.agents.memory_agent import MemoryAgent
from omega.agents.planner import PlannerAgent
from omega.agents.research import ResearchAgent
from omega.agents.terminal_agent import TerminalAgent
from omega.schema import MemoryKind, Task, TaskResult, TaskStatus, TaskType


class ExecutorAgent:
    """Coordinates OMEGA specialist agents and persists execution state."""

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.agents = {
            "planner": PlannerAgent(context),
            "research": ResearchAgent(context),
            "coding": CodingAgent(context),
            "browser": BrowserAgent(context),
            "terminal": TerminalAgent(context),
            "devops": DevOpsAgent(context),
            "memory": MemoryAgent(context),
            "critic": CriticAgent(context),
        }

    async def execute_goal(self, goal: str) -> dict[str, object]:
        started = datetime.now(UTC)
        root_task = Task(goal=goal, task_type=TaskType.PLANNING, assigned_agent="planner")
        planner_result = await self.agents["planner"].run(root_task)
        self.context.memory.add_task_result(planner_result)
        subtasks = [Task.model_validate(item) for item in planner_result.artifacts.get("subtasks", [])]

        semaphore = asyncio.Semaphore(self.context.settings.max_parallel_agents)

        async def run_one(task: Task) -> TaskResult:
            async with semaphore:
                return await self.run_task(task)

        non_critic = [task for task in subtasks if task.assigned_agent != "critic"]
        critic_tasks = [task for task in subtasks if task.assigned_agent == "critic"]
        results = await asyncio.gather(*(run_one(task) for task in non_critic), return_exceptions=True)

        task_results: list[TaskResult] = [planner_result]
        for task, result in zip(non_critic, results, strict=False):
            if isinstance(result, Exception):
                task_result = TaskResult(
                    task_id=task.id,
                    agent=task.assigned_agent or "unknown",
                    status=TaskStatus.FAILED,
                    summary=str(result),
                )
            else:
                task_result = result
            self.context.memory.add_task_result(task_result)
            task_results.append(task_result)

        for critic_task in critic_tasks:
            combined = "\n\n".join(f"{result.agent}: {result.summary}" for result in task_results)
            critic_task.goal = f"{critic_task.goal}\n\nResults to review:\n{combined}"
            critic_result = await self.run_task(critic_task)
            self.context.memory.add_task_result(critic_result)
            task_results.append(critic_result)

        finished = datetime.now(UTC)
        success = all(result.status == TaskStatus.SUCCEEDED for result in task_results)
        self.context.memory.remember(
            f"Executed goal: {goal}",
            kind=MemoryKind.EPISODIC,
            tags=["execution", "goal", "success" if success else "failed"],
            metadata={
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "results": [result.model_dump(mode="json") for result in task_results],
            },
            importance=0.7,
        )
        return {
            "goal": goal,
            "success": success,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "results": [result.model_dump(mode="json") for result in task_results],
        }

    async def run_task(self, task: Task) -> TaskResult:
        agent_name = task.assigned_agent or self._agent_for_task(task.task_type)
        agent = self.agents.get(agent_name)
        if not agent:
            return TaskResult(
                task_id=task.id,
                agent=agent_name,
                status=TaskStatus.FAILED,
                summary=f"No agent registered for '{agent_name}'.",
            )
        try:
            return await agent.run(task)
        except Exception as exc:
            return TaskResult(task_id=task.id, agent=agent_name, status=TaskStatus.FAILED, summary=str(exc))

    def _agent_for_task(self, task_type: TaskType) -> str:
        return {
            TaskType.PLANNING: "planner",
            TaskType.RESEARCH: "research",
            TaskType.CODING: "coding",
            TaskType.BROWSER: "browser",
            TaskType.DEVOPS: "devops",
            TaskType.MEMORY: "memory",
            TaskType.CRITIC: "critic",
        }.get(task_type, "critic")
