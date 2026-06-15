from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omega.config import OmegaSettings
from omega.memory import MemoryStore
from omega.permissions import PermissionPolicy
from omega.schema import PluginResult


class PluginExecutionError(RuntimeError):
    """Raised when a plugin cannot complete an action."""


@dataclass
class PluginContext:
    settings: OmegaSettings
    memory: MemoryStore
    permissions: PermissionPolicy
    workspace: Path


class Plugin(ABC):
    name: str
    description: str
    actions: dict[str, str]

    @abstractmethod
    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        raise NotImplementedError

    def unknown_action(self, action: str) -> PluginResult:
        return PluginResult(
            plugin=self.name,
            action=action,
            ok=False,
            error=f"Unknown action '{action}' for plugin '{self.name}'.",
        )
