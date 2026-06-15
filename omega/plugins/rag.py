from __future__ import annotations

from typing import Any

from omega.schema import MemoryKind, PluginResult
from omega.plugins.base import Plugin, PluginContext


class RAGPlugin(Plugin):
    name = "rag"
    description = "Store and retrieve knowledge from OMEGA memory."
    actions = {
        "remember": "Persist a memory item.",
        "recall": "Retrieve relevant memories.",
        "recent": "List recent memory records.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "remember":
            record = context.memory.remember(
                str(arguments["content"]),
                kind=MemoryKind(arguments.get("kind", MemoryKind.LONG_TERM.value)),
                tags=list(arguments.get("tags", [])),
                metadata=dict(arguments.get("metadata", {})),
                importance=float(arguments.get("importance", 0.5)),
            )
            return PluginResult(plugin=self.name, action=action, ok=True, data=record.model_dump(mode="json"))
        if action == "recall":
            kind = arguments.get("kind")
            results = context.memory.search(
                str(arguments["query"]),
                kind=MemoryKind(kind) if kind else None,
                limit=int(arguments.get("limit", 10)),
            )
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=True,
                data=[{"record": record.model_dump(mode="json"), "score": score} for record, score in results],
            )
        if action == "recent":
            kind = arguments.get("kind")
            records = context.memory.recent(
                kind=MemoryKind(kind) if kind else None,
                limit=int(arguments.get("limit", 20)),
            )
            return PluginResult(plugin=self.name, action=action, ok=True, data=[record.model_dump(mode="json") for record in records])
        return self.unknown_action(action)
