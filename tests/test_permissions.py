from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omega.permissions import ApprovalRequired, PermissionPolicy


class PermissionPolicyTests(unittest.TestCase):
    def test_denies_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = PermissionPolicy.default(Path(tmp))
            self.assertFalse(policy.path_allowed("../outside.txt"))

    def test_write_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = PermissionPolicy.default(Path(tmp))
            with self.assertRaises(ApprovalRequired):
                policy.ensure_allowed("filesystem", "write", {"path": "file.txt"})
            policy.ensure_allowed("filesystem", "write", {"path": "file.txt"}, approved=True)


if __name__ == "__main__":
    unittest.main()
