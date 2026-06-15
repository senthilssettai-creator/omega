from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from omega.memory import MemoryStore
from omega.schema import MemoryKind


@dataclass
class ImprovementProposal:
    id: str
    title: str
    rationale: str
    proposed_actions: list[str]
    requires_approval: bool = True


class SelfImprovementEngine:
    """Analyzes execution history and records improvement proposals for user approval."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def analyze(self, limit: int = 50) -> ImprovementProposal:
        history = self.memory.task_history(limit=limit)
        failures = [item for item in history if item["status"] != "succeeded"]
        agents = Counter(item["agent"] for item in failures)
        if failures:
            common_agent, count = agents.most_common(1)[0]
            title = f"Reduce {common_agent} failures"
            rationale = f"{count} recent failed task results came from {common_agent}."
            actions = [
                f"Review recent {common_agent} task summaries.",
                "Add a focused test or permission rule for the recurring failure mode.",
                "Apply a patch only after explicit user approval.",
            ]
        else:
            title = "Increase verification depth"
            rationale = "No recent failures were recorded, so the best improvement is stronger routine verification."
            actions = [
                "Run compile and unit tests after code-generating goals.",
                "Store benchmark results as episodic memory.",
                "Promote stable workflows to procedural memory.",
            ]
        proposal = ImprovementProposal(id=str(uuid4()), title=title, rationale=rationale, proposed_actions=actions)
        self.memory.remember(
            f"Self-improvement proposal: {title}\n{rationale}",
            kind=MemoryKind.PROCEDURAL,
            tags=["self-improvement", "proposal"],
            metadata=proposal.__dict__,
            importance=0.65,
        )
        return proposal

    def approve_record(self, proposal_id: str, decision: str, metadata: dict[str, Any] | None = None) -> None:
        self.memory.remember(
            f"Self-improvement approval decision for {proposal_id}: {decision}",
            kind=MemoryKind.EPISODIC,
            tags=["self-improvement", "approval", decision],
            metadata=metadata or {},
            importance=0.7,
        )
