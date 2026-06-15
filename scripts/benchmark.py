from __future__ import annotations

import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omega.memory import MemoryStore
from omega.schema import MemoryKind


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(Path(tmp) / "omega.sqlite3")
        for index in range(250):
            store.remember(
                f"Benchmark memory item {index} about planning coding browser research and devops.",
                kind=MemoryKind.SEMANTIC,
                tags=["benchmark", "memory"],
            )
        samples = []
        for _ in range(25):
            started = time.perf_counter()
            store.search("coding research memory", limit=10)
            samples.append((time.perf_counter() - started) * 1000)
        print(
            {
                "mean_ms": round(statistics.mean(samples), 3),
                "p95_ms": round(sorted(samples)[int(len(samples) * 0.95) - 1], 3),
                "target_ms": 200,
            }
        )
        store.close()


if __name__ == "__main__":
    main()
