from __future__ import annotations

from omega.agents.base import Agent
from omega.schema import MemoryKind, Task, TaskResult, TaskType


class PlannerAgent(Agent):
    name = "planner"
    system_prompt = (
        "You are OMEGA's planner. Convert goals into concrete subtasks for specialist agents. "
        "Return rationale summaries, dependencies, and acceptance checks without exposing private chain of thought."
    )

    async def run(self, task: Task) -> TaskResult:
        plan = self.plan(task.goal)
        self.context.memory.remember(
            f"Planned goal: {task.goal}",
            kind=MemoryKind.EPISODIC,
            tags=["plan", "goal"],
            metadata={"task_id": task.id, "subtasks": [item.model_dump(mode="json") for item in plan]},
        )
        summary = "\n".join(f"{index + 1}. {item.assigned_agent}: {item.goal}" for index, item in enumerate(plan))
        return self.result(task, f"Created {len(plan)} executable subtasks.\n{summary}", artifacts={"subtasks": [item.model_dump(mode="json") for item in plan]})

    def plan(self, goal: str) -> list[Task]:
        normalized = goal.lower()
        tasks: list[Task] = [
            Task(goal=f"Recall useful memories and user preferences for: {goal}", task_type=TaskType.MEMORY, assigned_agent="memory"),
            Task(goal=f"Research constraints, references, and current context for: {goal}", task_type=TaskType.RESEARCH, assigned_agent="research"),
        ]
        if any(word in normalized for word in ["code", "app", "build", "fix", "refactor", "test", "project"]):
            tasks.append(Task(goal=f"Design and implement code changes or artifacts for: {goal}", task_type=TaskType.CODING, assigned_agent="coding"))
        if any(word in normalized for word in ["browser", "website", "form", "login", "page", "web", "search", "canva", "youtube", "upload", "download", "chrome", "tab"]):
            tasks.append(Task(goal=f"Use browser automation where useful for: {goal}", task_type=TaskType.BROWSER, assigned_agent="browser"))
        if any(word in normalized for word in ["terminal", "command", "run", "execute", "install", "configure", "tweak", "optimize", "settings", "fps", "performance"]):
            tasks.append(Task(goal=f"Determine a safe terminal command to support: {goal}", task_type=TaskType.EXECUTION, assigned_agent="terminal"))
        if any(word in normalized for word in ["deploy", "docker", "ci", "git", "infrastructure", "server"]):
            tasks.append(Task(goal=f"Prepare DevOps, repository, and deployment support for: {goal}", task_type=TaskType.DEVOPS, assigned_agent="devops"))
        tasks.append(Task(goal=f"Review the combined work for risks, gaps, and verification needs for: {goal}", task_type=TaskType.CRITIC, assigned_agent="critic"))
        return tasks
