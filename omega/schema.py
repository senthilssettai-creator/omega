from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    PLANNING = "planning"
    RESEARCH = "research"
    CODING = "coding"
    BROWSER = "browser"
    DEVOPS = "devops"
    MEMORY = "memory"
    CRITIC = "critic"
    EXECUTION = "execution"
    FAST = "fast"
    LONG_CONTEXT = "long_context"


class MemoryKind(StrEnum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    USER = "user"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class PermissionDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"


class AgentMessage(BaseModel):
    role: str
    content: str
    name: str | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    goal: str
    task_type: TaskType = TaskType.EXECUTION
    assigned_agent: str | None = None
    parent_id: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaskResult(BaseModel):
    task_id: str
    agent: str
    status: TaskStatus
    summary: str
    artifacts: dict[str, Any] = Field(default_factory=dict)
    messages: list[AgentMessage] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: MemoryKind
    content: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModelChoice(BaseModel):
    task_type: TaskType
    model: str
    reason: str
    provider: str = "openrouter"


class PluginCall(BaseModel):
    plugin: str
    action: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class PluginResult(BaseModel):
    plugin: str
    action: str
    ok: bool
    data: Any = None
    error: str | None = None
