from __future__ import annotations

import asyncio
import sys
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class TerminalPlugin(Plugin):
    name = "terminal"
    description = "Execute terminal commands and sandboxed Python or Node snippets."
    actions = {
        "run": "Run a shell command in the workspace.",
        "python_sandbox": "Run isolated Python code with python -I.",
        "node_sandbox": "Run Node.js code with node -e.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        timeout = int(arguments.get("timeout", context.settings.command_timeout_seconds))
        cwd = context.permissions.resolve_path(arguments.get("cwd", "."))
        if action == "run":
            return await self._run_shell(str(arguments["command"]), cwd, timeout)
        if action == "python_sandbox":
            code = str(arguments.get("code", ""))
            return await self._run_exec([sys.executable, "-I", "-c", code], cwd, timeout, action)
        if action == "node_sandbox":
            code = str(arguments.get("code", ""))
            return await self._run_exec(["node", "-e", code], cwd, timeout, action)
        return self.unknown_action(action)

    async def _run_shell(self, command: str, cwd, timeout: int) -> PluginResult:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError:
            process.kill()
            await process.communicate()
            return PluginResult(plugin=self.name, action="run", ok=False, error=f"Command timed out after {timeout}s.")
        return PluginResult(
            plugin=self.name,
            action="run",
            ok=process.returncode == 0,
            data={"returncode": process.returncode, "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")},
            error=None if process.returncode == 0 else f"Command exited with {process.returncode}.",
        )

    async def _run_exec(self, argv: list[str], cwd, timeout: int, action: str) -> PluginResult:
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            return PluginResult(plugin=self.name, action=action, ok=False, error=str(exc))
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError:
            process.kill()
            await process.communicate()
            return PluginResult(plugin=self.name, action=action, ok=False, error=f"Sandbox timed out after {timeout}s.")
        return PluginResult(
            plugin=self.name,
            action=action,
            ok=process.returncode == 0,
            data={"returncode": process.returncode, "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace")},
            error=None if process.returncode == 0 else f"Sandbox exited with {process.returncode}.",
        )
