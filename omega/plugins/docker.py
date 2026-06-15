from __future__ import annotations

import asyncio
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class DockerPlugin(Plugin):
    name = "docker"
    description = "Operate Docker through the local Docker CLI."
    actions = {
        "ps": "List containers.",
        "images": "List images.",
        "compose_up": "Run docker compose up.",
        "compose_down": "Run docker compose down.",
        "container_remove": "Remove a container.",
        "image_remove": "Remove an image.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        cwd = context.permissions.resolve_path(arguments.get("cwd", "."))
        if action == "ps":
            return await self._docker(["ps", "--format", "json"], cwd, action)
        if action == "images":
            return await self._docker(["images", "--format", "json"], cwd, action)
        if action == "compose_up":
            args = ["compose", "up", "-d"]
            if arguments.get("file"):
                args[1:1] = ["-f", str(arguments["file"])]
            return await self._docker(args, cwd, action)
        if action == "compose_down":
            args = ["compose", "down"]
            if arguments.get("file"):
                args[1:1] = ["-f", str(arguments["file"])]
            return await self._docker(args, cwd, action)
        if action == "container_remove":
            return await self._docker(["rm", "-f", str(arguments["container"])], cwd, action)
        if action == "image_remove":
            return await self._docker(["rmi", str(arguments["image"])], cwd, action)
        return self.unknown_action(action)

    async def _docker(self, args: list[str], cwd, action: str) -> PluginResult:
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                *args,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return PluginResult(plugin=self.name, action=action, ok=False, error="docker executable not found.")
        stdout, stderr = await process.communicate()
        return PluginResult(
            plugin=self.name,
            action=action,
            ok=process.returncode == 0,
            data={"stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"), "returncode": process.returncode},
            error=None if process.returncode == 0 else f"docker exited with {process.returncode}.",
        )
