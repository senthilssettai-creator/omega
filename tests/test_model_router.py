from __future__ import annotations

import unittest

from omega.model_router import ModelRouter
from omega.schema import TaskType


class ModelRouterTests(unittest.TestCase):
    def test_routes_coding_to_free_model(self) -> None:
        choice = ModelRouter().choose(TaskType.CODING)
        self.assertIn(":free", choice.model)


if __name__ == "__main__":
    unittest.main()
