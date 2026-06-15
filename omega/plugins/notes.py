from __future__ import annotations

from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import MemoryKind, PluginResult


class NotesPlugin(Plugin):
    name = "notes"
    description = "Create and search durable notes stored in OMEGA memory."
    actions = {
        "create": "Create a note.",
        "search": "Search notes.",
        "recent": "List recent notes.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "create":
            title = str(arguments.get("title", "Untitled"))
            body = str(arguments.get("body", ""))
            record = context.memory.remember(
                f"{title}\n\n{body}",
                kind=MemoryKind.SEMANTIC,
                tags=["note", *list(arguments.get("tags", []))],
                metadata={"title": title},
                importance=float(arguments.get("importance", 0.5)),
            )
            return PluginResult(plugin=self.name, action=action, ok=True, data=record.model_dump(mode="json"))
        if action == "search":
            results = context.memory.search(str(arguments["query"]), kind=MemoryKind.SEMANTIC, limit=int(arguments.get("limit", 10)))
            data = [
                {"record": record.model_dump(mode="json"), "score": score}
                for record, score in results
                if "note" in record.tags
            ]
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        if action == "recent":
            data = [
                record.model_dump(mode="json")
                for record in context.memory.recent(kind=MemoryKind.SEMANTIC, limit=int(arguments.get("limit", 20)))
                if "note" in record.tags
            ]
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        return self.unknown_action(action)
