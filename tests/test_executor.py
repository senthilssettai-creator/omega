from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from omega.config import OmegaSettings
from omega.agents.planner import PlannerAgent
from omega.agents.base import AgentContext
from omega.memory import MemoryStore
from omega.model_router import ModelRouter
from omega.openrouter import OpenRouterClient
from omega.permissions import PermissionPolicy
from omega.plugins.registry import PluginRegistry
from omega.runtime import OmegaRuntime
from omega.schema import Task, TaskType


class ExecutorTests(unittest.TestCase):
    def test_execute_goal_without_model_key(self) -> None:
        async def scenario() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                workspace = root / "workspace"
                workspace.mkdir()
                settings = OmegaSettings(home_dir=root / "home", workspace=workspace, openrouter_api_key=None)
                runtime = OmegaRuntime.create(settings=settings)
                try:
                    result = await runtime.execute_goal("build a small Python app")
                    self.assertTrue(result["success"])
                    self.assertGreaterEqual(len(result["results"]), 4)
                finally:
                    runtime.close()

        asyncio.run(scenario())

    def test_planner_routes_open_chrome_to_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            settings = OmegaSettings(home_dir=root / "home", workspace=workspace, openrouter_api_key=None)
            settings.ensure_directories()
            memory = MemoryStore(settings.memory_db_path)
            permissions = PermissionPolicy.default(workspace)
            plugins = PluginRegistry(settings, memory, permissions)
            context = AgentContext(
                settings=settings,
                memory=memory,
                model_router=ModelRouter(),
                openrouter=OpenRouterClient(None),
                plugins=plugins,
            )
            planner = PlannerAgent(context)
            tasks = planner.plan("open chrome")
            self.assertTrue(any(task.assigned_agent == "browser" and task.task_type == TaskType.BROWSER for task in tasks))
            memory.close()


if __name__ == "__main__":
    unittest.main()
