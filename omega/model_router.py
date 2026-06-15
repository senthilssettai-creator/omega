from __future__ import annotations

import json
from pathlib import Path

from omega.schema import ModelChoice, TaskType


DEFAULT_MODELS: dict[str, list[str]] = {
    TaskType.PLANNING.value: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openai/gpt-oss-120b:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openrouter/free",
    ],
    TaskType.RESEARCH.value: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openai/gpt-oss-120b:free",
        "google/gemma-4-31b-it:free",
        "openrouter/free",
    ],
    TaskType.CODING.value: [
        "qwen/qwen3-coder:free",
        "openai/gpt-oss-120b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openrouter/free",
    ],
    TaskType.FAST.value: [
        "google/gemma-4-26b-a4b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "openrouter/free",
    ],
    TaskType.LONG_CONTEXT.value: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openai/gpt-oss-120b:free",
        "openrouter/free",
    ],
    TaskType.BROWSER.value: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openai/gpt-oss-120b:free",
        "openrouter/free",
    ],
    TaskType.DEVOPS.value: [
        "qwen/qwen3-coder:free",
        "openai/gpt-oss-120b:free",
        "openrouter/free",
    ],
    TaskType.MEMORY.value: [
        "google/gemma-4-26b-a4b-it:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openrouter/free",
    ],
    TaskType.CRITIC.value: [
        "openai/gpt-oss-120b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openrouter/free",
    ],
    TaskType.EXECUTION.value: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "openai/gpt-oss-120b:free",
        "openrouter/free",
    ],
}


class ModelRouter:
    """Selects free OpenRouter models by task type."""

    def __init__(self, model_file: Path | None = None) -> None:
        self.models = DEFAULT_MODELS.copy()
        if model_file and model_file.exists():
            loaded = json.loads(model_file.read_text(encoding="utf-8"))
            for key, value in loaded.items():
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    self.models[key] = value

    def choose(self, task_type: TaskType, *, prefer_long_context: bool = False) -> ModelChoice:
        route = TaskType.LONG_CONTEXT if prefer_long_context else task_type
        candidates = self.candidates(route)
        model = candidates[0]
        return ModelChoice(
            task_type=route,
            model=model,
            reason=f"Selected first configured free model for {route.value}: {model}",
        )

    def candidates(self, task_type: TaskType, *, prefer_long_context: bool = False) -> list[str]:
        route = TaskType.LONG_CONTEXT if prefer_long_context else task_type
        candidates = self.models.get(route.value) or self.models[TaskType.EXECUTION.value]
        return list(dict.fromkeys([*candidates, "openrouter/free"]))
