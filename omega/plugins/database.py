from __future__ import annotations

import sqlite3
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class DatabasePlugin(Plugin):
    name = "database"
    description = "Query SQLite databases inside the workspace."
    actions = {
        "query_readonly": "Run a read-only SQLite query.",
        "query_write": "Run a SQLite write query.",
        "schema": "Inspect database tables and columns.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        db_path = context.permissions.resolve_path(arguments["db_path"])
        if action == "schema":
            with sqlite3.connect(db_path) as connection:
                tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                data = {
                    table[0]: connection.execute(f"PRAGMA table_info({table[0]})").fetchall()
                    for table in tables
                }
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        if action in {"query_readonly", "query_write"}:
            sql = str(arguments["sql"]).strip()
            readonly_tokens = ("select", "pragma", "with", "explain")
            if action == "query_readonly" and not sql.lower().startswith(readonly_tokens):
                return PluginResult(plugin=self.name, action=action, ok=False, error="Read-only queries must start with SELECT, WITH, PRAGMA, or EXPLAIN.")
            with sqlite3.connect(db_path) as connection:
                cursor = connection.execute(sql, arguments.get("parameters", []))
                rows = cursor.fetchall()
                columns = [item[0] for item in cursor.description or []]
                if action == "query_write":
                    connection.commit()
            return PluginResult(plugin=self.name, action=action, ok=True, data={"columns": columns, "rows": rows})
        return self.unknown_action(action)
