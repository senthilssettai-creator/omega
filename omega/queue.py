from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class LocalTaskQueue:
    """Async in-process queue used when Redis/Celery are not configured."""

    def __init__(self, workers: int = 2) -> None:
        self.queue: asyncio.Queue[tuple[Callable[..., Awaitable[Any]], tuple, dict]] = asyncio.Queue()
        self.workers = workers
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        for _ in range(self.workers):
            self._tasks.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def submit(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> None:
        await self.queue.put((func, args, kwargs))

    async def _worker(self) -> None:
        while True:
            func, args, kwargs = await self.queue.get()
            try:
                await func(*args, **kwargs)
            finally:
                self.queue.task_done()


def create_celery_app(broker_url: str, result_backend: str):
    try:
        from celery import Celery
    except ImportError as exc:
        raise RuntimeError("celery is not installed.") from exc
    return Celery("omega", broker=broker_url, backend=result_backend)
