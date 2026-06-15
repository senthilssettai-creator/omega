from __future__ import annotations

import asyncio
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class GitPlugin(Plugin):
    name = "git"
    description = "Inspect and operate on Git repositories in the workspace."
    actions = {
        "status": "Show short repository status.",
        "diff": "Show repository diff.",
        "log": "Show recent commits.",
        "branch": "Create or switch branches.",
        "commit": "Create a commit from staged changes.",
        "push": "Push the current branch.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        cwd = context.permissions.resolve_path(arguments.get("cwd", "."))
        if action == "status":
            return await self._git(["status", "--short"], cwd, action)
        if action == "diff":
            return await self._git(["diff", "--", "."], cwd, action)
        if action == "log":
            limit = str(int(arguments.get("limit", 10)))
            return await self._git(["log", f"-{limit}", "--oneline"], cwd, action)
        if action == "branch":
            branch = str(arguments["name"])
            create = bool(arguments.get("create", False))
            args = ["switch", "-c", branch] if create else ["switch", branch]
            return await self._git(args, cwd, action)
        if action == "commit":
            message = str(arguments["message"])
            return await self._git(["commit", "-m", message], cwd, action)
        if action == "push":
            remote = str(arguments.get("remote", "origin"))
            branch = str(arguments.get("branch", "HEAD"))
            return await self._git(["push", remote, branch], cwd, action)
        return self.unknown_action(action)

    async def _git(self, args: list[str], cwd, action: str) -> PluginResult:
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                *args,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return PluginResult(plugin=self.name, action=action, ok=False, error="git executable not found.")
        stdout, stderr = await process.communicate()
        return PluginResult(
            plugin=self.name,
            action=action,
            ok=process.returncode == 0,
            data={"stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"), "returncode": process.returncode},
            error=None if process.returncode == 0 else f"git exited with {process.returncode}.",
        )
