from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omega.memory import MemoryStore
from omega.schema import MemoryKind


class MemoryStoreTests(unittest.TestCase):
    def test_remember_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(Path(tmp) / "memory.sqlite3")
            record = store.remember("OMEGA can plan and execute coding tasks.", kind=MemoryKind.SEMANTIC, tags=["omega", "coding"])
            results = store.search("coding plan", kind=MemoryKind.SEMANTIC)
            self.assertEqual(results[0][0].id, record.id)
            self.assertGreater(results[0][1], 0)
            store.close()


if __name__ == "__main__":
    unittest.main()
