from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class FilesystemPlugin(Plugin):
    name = "filesystem"
    description = "Read, write, search, move, and delete files inside the configured workspace."
    actions = {
        "list": "List files under a workspace path.",
        "read": "Read a text file.",
        "write": "Write a text or binary file.",
        "append": "Append text to a file.",
        "delete": "Delete a file or directory.",
        "move": "Move a file or directory.",
        "search": "Search file names and optionally file contents.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "list":
            path = context.permissions.resolve_path(arguments.get("path", "."))
            recursive = bool(arguments.get("recursive", False))
            pattern = str(arguments.get("pattern", "*"))
            iterator = path.rglob(pattern) if recursive else path.glob(pattern)
            data = [
                {
                    "path": item.relative_to(context.workspace).as_posix(),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                }
                for item in sorted(iterator)
            ]
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        if action == "read":
            path = context.permissions.resolve_path(arguments["path"])
            data = path.read_text(encoding=arguments.get("encoding", "utf-8"))
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        if action == "write":
            path = context.permissions.resolve_path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            content = arguments.get("content", "")
            path.write_text(str(content), encoding=arguments.get("encoding", "utf-8"))
            return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(path), "bytes": path.stat().st_size})
        if action == "append":
            path = context.permissions.resolve_path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding=arguments.get("encoding", "utf-8")) as handle:
                handle.write(str(arguments.get("content", "")))
            return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(path), "bytes": path.stat().st_size})
        if action == "delete":
            path = context.permissions.resolve_path(arguments["path"])
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            return PluginResult(plugin=self.name, action=action, ok=True, data={"deleted": str(path)})
        if action == "move":
            source = context.permissions.resolve_path(arguments["source"])
            destination = context.permissions.resolve_path(arguments["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return PluginResult(plugin=self.name, action=action, ok=True, data={"source": str(source), "destination": str(destination)})
        if action == "search":
            root = context.permissions.resolve_path(arguments.get("path", "."))
            pattern = str(arguments.get("pattern", "*"))
            text = arguments.get("text")
            matches: list[dict[str, Any]] = []
            for item in root.rglob(pattern):
                if not item.is_file():
                    continue
                relative = item.relative_to(context.workspace).as_posix()
                if text is None:
                    matches.append({"path": relative, "line": None, "preview": None})
                    continue
                try:
                    for index, line in enumerate(item.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                        if str(text).lower() in line.lower():
                            matches.append({"path": relative, "line": index, "preview": line.strip()[:240]})
                except OSError:
                    continue
            return PluginResult(plugin=self.name, action=action, ok=True, data=matches[: int(arguments.get("limit", 100))])
        return self.unknown_action(action)
