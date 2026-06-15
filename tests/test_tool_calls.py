from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from omega.config import OmegaSettings
from omega.memory import MemoryStore
from omega.permissions import PermissionPolicy
from omega.plugins.registry import PluginRegistry
from omega.tool_calls import execute_tool_calls, parse_tool_calls


class ToolCallTests(unittest.TestCase):
    def test_parse_model_tool_call_tags(self) -> None:
        calls = parse_tool_calls(
            '<tool_call>read_file path="README.md" />\n'
            '<tool_call>shell command="ls -la omega/" />\n'
            '<tool_call name="open_browser" browser="chrome" url="https://example.com" />'
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0].plugin, "filesystem")
        self.assertEqual(calls[1].plugin, "terminal")
        self.assertEqual(calls[2].plugin, "browser")

    def test_execute_read_file_tool_call(self) -> None:
        async def scenario() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                workspace = root / "workspace"
                workspace.mkdir()
                (workspace / "note.txt").write_text("hello", encoding="utf-8")
                settings = OmegaSettings(home_dir=root / "home", workspace=workspace)
                settings.ensure_directories()
                memory = MemoryStore(settings.memory_db_path)
                registry = PluginRegistry(settings, memory, PermissionPolicy.default(workspace))
                registry.register_builtins()
                executions = await execute_tool_calls(
                    '<tool_call>read_file path="note.txt" />',
                    registry,
                )
                self.assertEqual(executions[0]["result"]["data"], "hello")
                memory.close()

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
