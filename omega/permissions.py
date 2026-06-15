from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omega.schema import PermissionDecision


class PermissionError(RuntimeError):
    """Raised when a requested action violates OMEGA's permission policy."""


class ApprovalRequired(PermissionError):
    """Raised when a requested action needs explicit user approval."""


@dataclass(frozen=True)
class PermissionRule:
    plugin: str
    action: str
    decision: PermissionDecision
    path_glob: str | None = None

    def matches(self, plugin: str, action: str, path: str | None = None) -> bool:
        plugin_ok = self.plugin == "*" or self.plugin == plugin
        action_ok = self.action == "*" or self.action == action
        path_ok = True if self.path_glob is None or path is None else fnmatch.fnmatch(path, self.path_glob)
        return plugin_ok and action_ok and path_ok


class PermissionPolicy:
    """Configurable allow, deny, and approval policy for tool execution."""

    destructive_actions = {
        "delete",
        "move",
        "write",
        "run",
        "commit",
        "push",
        "container_remove",
        "image_remove",
        "send",
        "upload",
    }
    destructive_command_fragments = [
        "rm -rf",
        "del /s",
        "format ",
        "mkfs",
        "shutdown",
        "reboot",
        "git reset --hard",
        "git clean -fd",
    ]

    def __init__(self, workspace: Path, *, rules: list[PermissionRule] | None = None) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.rules = rules or []

    @classmethod
    def from_file(cls, path: Path, workspace: Path) -> "PermissionPolicy":
        if not path.exists():
            return cls.default(workspace)
        data = json.loads(path.read_text(encoding="utf-8"))
        rules = [
            PermissionRule(
                plugin=item.get("plugin", "*"),
                action=item.get("action", "*"),
                decision=PermissionDecision(item["decision"]),
                path_glob=item.get("path_glob"),
            )
            for item in data.get("rules", [])
        ]
        return cls(workspace, rules=rules)

    @classmethod
    def default(cls, workspace: Path) -> "PermissionPolicy":
        return cls(
            workspace,
            rules=[
                PermissionRule("*", "read", PermissionDecision.ALLOW),
                PermissionRule("*", "list", PermissionDecision.ALLOW),
                PermissionRule("*", "search", PermissionDecision.ALLOW),
                PermissionRule("memory", "*", PermissionDecision.ALLOW),
                PermissionRule("rag", "*", PermissionDecision.ALLOW),
                PermissionRule("database", "query_readonly", PermissionDecision.ALLOW),
                PermissionRule("git", "status", PermissionDecision.ALLOW),
                PermissionRule("git", "diff", PermissionDecision.ALLOW),
                PermissionRule("git", "log", PermissionDecision.ALLOW),
                PermissionRule("search", "*", PermissionDecision.ALLOW),
            ],
        )

    def evaluate(self, plugin: str, action: str, arguments: dict[str, Any] | None = None) -> PermissionDecision:
        arguments = arguments or {}
        path = self._argument_path(arguments)
        if path and not self.path_allowed(path):
            return PermissionDecision.DENY
        for rule in self.rules:
            if rule.matches(plugin, action, path):
                return rule.decision
        command = str(arguments.get("command", "")).lower()
        if action in self.destructive_actions:
            return PermissionDecision.REQUIRE_CONFIRMATION
        if any(fragment in command for fragment in self.destructive_command_fragments):
            return PermissionDecision.REQUIRE_CONFIRMATION
        return PermissionDecision.ALLOW

    def ensure_allowed(
        self,
        plugin: str,
        action: str,
        arguments: dict[str, Any] | None = None,
        *,
        approved: bool = False,
    ) -> None:
        decision = self.evaluate(plugin, action, arguments)
        if decision == PermissionDecision.DENY:
            raise PermissionError(f"Permission denied for {plugin}.{action}.")
        if decision == PermissionDecision.REQUIRE_CONFIRMATION and not approved:
            raise ApprovalRequired(f"Approval required for {plugin}.{action}.")

    def path_allowed(self, raw_path: str | Path) -> bool:
        try:
            resolved = (self.workspace / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        except OSError:
            return False
        return resolved == self.workspace or self.workspace in resolved.parents

    def resolve_path(self, raw_path: str | Path) -> Path:
        resolved = (self.workspace / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        if not self.path_allowed(resolved):
            raise PermissionError(f"Path escapes workspace: {raw_path}")
        return resolved

    def _argument_path(self, arguments: dict[str, Any]) -> str | None:
        for key in ("path", "source", "destination", "file", "db_path"):
            value = arguments.get(key)
            if isinstance(value, str):
                return value
        return None
