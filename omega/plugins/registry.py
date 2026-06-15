from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from omega.config import OmegaSettings
from omega.memory import MemoryStore
from omega.permissions import PermissionPolicy
from omega.plugins.base import Plugin, PluginContext
from omega.plugins.builtin import builtin_plugins
from omega.schema import PluginCall, PluginResult


class PluginRegistry:
    """Runtime plugin registry with safe permission checks and dynamic discovery."""

    def __init__(self, settings: OmegaSettings, memory: MemoryStore, permissions: PermissionPolicy) -> None:
        self.settings = settings
        self.memory = memory
        self.permissions = permissions
        self.plugins: dict[str, Plugin] = {}
        self.context = PluginContext(
            settings=settings,
            memory=memory,
            permissions=permissions,
            workspace=settings.resolved_workspace(),
        )

    def register(self, plugin: Plugin) -> None:
        self.plugins[plugin.name] = plugin

    def register_builtins(self) -> None:
        for plugin in builtin_plugins():
            self.register(plugin)

    def discover_dynamic(self) -> list[str]:
        loaded: list[str] = []
        plugin_dir = self.settings.plugins_dir
        plugin_dir.mkdir(parents=True, exist_ok=True)
        for file in sorted(plugin_dir.glob("*.py")):
            module_name = f"omega_user_plugin_{file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            factory = getattr(module, "omega_plugin", None)
            if callable(factory):
                plugin = factory()
                if isinstance(plugin, Plugin):
                    self.register(plugin)
                    loaded.append(plugin.name)
        return loaded

    def manifest(self) -> dict[str, Any]:
        return {
            name: {
                "description": plugin.description,
                "actions": plugin.actions,
            }
            for name, plugin in sorted(self.plugins.items())
        }

    async def call(self, call: PluginCall, *, approved: bool = False) -> PluginResult:
        plugin = self.plugins.get(call.plugin)
        if not plugin:
            return PluginResult(plugin=call.plugin, action=call.action, ok=False, error="Plugin not found.")
        self.permissions.ensure_allowed(call.plugin, call.action, call.arguments, approved=approved)
        return await plugin.call(call.action, call.arguments, self.context)
