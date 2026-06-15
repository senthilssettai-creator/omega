from __future__ import annotations

from datetime import datetime
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import MemoryKind, PluginResult


class CalendarPlugin(Plugin):
    name = "calendar"
    description = "Store and search local calendar events in persistent memory."
    actions = {
        "create_event": "Create an event.",
        "list_events": "List upcoming or matching events.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "create_event":
            title = str(arguments["title"])
            start = datetime.fromisoformat(str(arguments["start"]))
            end_raw = arguments.get("end")
            end = datetime.fromisoformat(str(end_raw)) if end_raw else None
            metadata = {
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat() if end else None,
                "location": arguments.get("location"),
            }
            record = context.memory.remember(
                f"Calendar event: {title} at {start.isoformat()}",
                kind=MemoryKind.PROCEDURAL,
                tags=["calendar", "event"],
                metadata=metadata,
                importance=0.6,
            )
            return PluginResult(plugin=self.name, action=action, ok=True, data=record.model_dump(mode="json"))
        if action == "list_events":
            query = str(arguments.get("query", "calendar event"))
            records = context.memory.search(query, kind=MemoryKind.PROCEDURAL, limit=int(arguments.get("limit", 20)))
            data = [
                record.model_dump(mode="json")
                for record, _score in records
                if "calendar" in record.tags
            ]
            data.sort(key=lambda item: item["metadata"].get("start") or "")
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        return self.unknown_action(action)
