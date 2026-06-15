from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render_goal_result(console: Console, result: dict[str, object]) -> None:
    console.print(Panel.fit(str(result["goal"]), title="OMEGA Goal", border_style="cyan"))
    table = Table(title="Agent Results")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Summary", overflow="fold")
    for item in result.get("results", []):
        row = dict(item)
        table.add_row(str(row.get("agent")), str(row.get("status")), str(row.get("summary", ""))[:900])
    console.print(table)


def render_plugins(console: Console, manifest: dict) -> None:
    table = Table(title="OMEGA Plugins")
    table.add_column("Plugin", style="cyan")
    table.add_column("Actions", overflow="fold")
    table.add_column("Description", overflow="fold")
    for name, data in manifest.items():
        table.add_row(name, ", ".join(data["actions"].keys()), data["description"])
    console.print(table)
