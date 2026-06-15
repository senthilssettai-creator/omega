from __future__ import annotations

from dataclasses import dataclass

from omega.agents.base import AgentContext
from omega.agents.executor import ExecutorAgent
from omega.config import OmegaSettings, load_settings
from omega.logging import configure_logging
from omega.memory import MemoryStore
from omega.model_router import ModelRouter
from omega.openrouter import OpenRouterClient
from omega.permissions import PermissionPolicy
from omega.plugins.registry import PluginRegistry
from omega.schema import PluginCall, PluginResult


@dataclass
class OmegaRuntime:
    settings: OmegaSettings
    memory: MemoryStore
    permissions: PermissionPolicy
    plugins: PluginRegistry
    model_router: ModelRouter
    openrouter: OpenRouterClient
    executor: ExecutorAgent

    @classmethod
    def create(cls, *, online: bool = False, approved: bool = False, settings: OmegaSettings | None = None) -> "OmegaRuntime":
        settings = settings or load_settings()
        configure_logging(settings.log_level)
        workspace = settings.resolved_workspace()
        memory = MemoryStore(settings.memory_db_path)
        permissions = PermissionPolicy.from_file(settings.permission_file, workspace)
        plugins = PluginRegistry(settings, memory, permissions)
        plugins.register_builtins()
        plugins.discover_dynamic()
        model_router = ModelRouter(settings.model_file)
        openrouter = OpenRouterClient(settings.openrouter_api_key, settings.openrouter_base_url)
        context = AgentContext(
            settings=settings,
            memory=memory,
            model_router=model_router,
            openrouter=openrouter,
            plugins=plugins,
            online=online,
            approved=approved,
        )
        executor = ExecutorAgent(context)
        return cls(
            settings=settings,
            memory=memory,
            permissions=permissions,
            plugins=plugins,
            model_router=model_router,
            openrouter=openrouter,
            executor=executor,
        )

    async def execute_goal(self, goal: str) -> dict[str, object]:
        return await self.executor.execute_goal(goal)

    async def call_plugin(self, plugin: str, action: str, arguments: dict, *, approved: bool = False) -> PluginResult:
        return await self.plugins.call(PluginCall(plugin=plugin, action=action, arguments=arguments), approved=approved)

    def close(self) -> None:
        self.memory.close()
