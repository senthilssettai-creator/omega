from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from omega.config import OmegaSettings
from omega.memory import MemoryStore
from omega.permissions import PermissionPolicy
from omega.plugins.registry import PluginRegistry
from omega.schema import PluginCall


class PluginRegistryTests(unittest.TestCase):
    def test_filesystem_write_and_read(self) -> None:
        async def scenario() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                workspace = root / "workspace"
                workspace.mkdir()
                settings = OmegaSettings(home_dir=root / "home", workspace=workspace)
                settings.ensure_directories()
                memory = MemoryStore(settings.memory_db_path)
                registry = PluginRegistry(settings, memory, PermissionPolicy.default(workspace))
                registry.register_builtins()
                write = await registry.call(
                    PluginCall(plugin="filesystem", action="write", arguments={"path": "hello.txt", "content": "hi"}),
                    approved=True,
                )
                read = await registry.call(PluginCall(plugin="filesystem", action="read", arguments={"path": "hello.txt"}))
                self.assertTrue(write.ok)
                self.assertEqual(read.data, "hi")
                memory.close()

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
