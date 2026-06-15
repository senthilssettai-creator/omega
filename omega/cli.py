from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

from omega.config import load_settings
from omega.runtime import OmegaRuntime
from omega.self_improvement import SelfImprovementEngine
from omega.tui import render_goal_result, render_plugins
from omega.workflows import load_workflow, run_workflow


CLI_LOGO = r"""
   ____  __  __  _____   ____    _____   _   _   
  / __ \|  \/  |/ ____| |  _ \  |_   _| | \ | |  
 | |  | | \  / | |  __  | |_) |   | |   |  \| |  
 | |  | | |\/| | | |_ | |  _ <    | |   | . ` |  
 | |__| | |  | | |__| | | |_) |  _| |_  | |\  |  
  \____/|_|  |_|\_____| |____/  |_____| |_| \_|  
"""

app = typer.Typer(help="OMEGA autonomous terminal AI agent.")
memory_app = typer.Typer(help="Memory commands.")
workflow_app = typer.Typer(help="Workflow commands.")
app.add_typer(memory_app, name="memory")
app.add_typer(workflow_app, name="workflow")
console = Console()


@app.command()
def init() -> None:
    settings = load_settings()
    settings.ensure_directories()
    console.print(Panel.fit(f"OMEGA initialized at {settings.home_dir.resolve()}", border_style="green"))


@app.command()
def run(
    goal: Annotated[str, typer.Argument(help="High-level goal for OMEGA to execute.")],
    online: Annotated[bool, typer.Option("--online", help="Allow web search where plugins permit it.")] = False,
    approved: Annotated[bool, typer.Option("--approved", help="Pre-approve confirmation-gated plugin actions.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print raw JSON.")] = False,
) -> None:
    async def _run() -> None:
        runtime = OmegaRuntime.create(online=online, approved=approved)
        try:
            console.print(Panel.fit(CLI_LOGO, title="OMEGA AI", border_style="bright_magenta"))
            with console.status("[cyan]OMEGA is planning and executing...[/cyan]"):
                result = await runtime.execute_goal(goal)
            if json_output:
                console.print(JSON(json.dumps(result)))
            else:
                render_goal_result(console, result)
        finally:
            runtime.close()

    asyncio.run(_run())


@app.command()
def plugins() -> None:
    runtime = OmegaRuntime.create()
    try:
        render_plugins(console, runtime.plugins.manifest())
    finally:
        runtime.close()


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Bind host.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Bind port.")] = 8765,
) -> None:
    import uvicorn

    uvicorn.run("omega.api:app", host=host, port=port, reload=False)


@app.command("improve")
def improve() -> None:
    runtime = OmegaRuntime.create()
    try:
        proposal = SelfImprovementEngine(runtime.memory).analyze()
        console.print(Panel.fit(proposal.title, title="Self-Improvement Proposal", border_style="yellow"))
        console.print(proposal.rationale)
        for action in proposal.proposed_actions:
            console.print(f"- {action}")
        console.print(f"Proposal ID: {proposal.id}")
    finally:
        runtime.close()


@memory_app.command("search")
def memory_search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    limit: Annotated[int, typer.Option(help="Maximum records.")] = 10,
) -> None:
    runtime = OmegaRuntime.create()
    try:
        results = runtime.memory.search(query, limit=limit)
        console.print(JSON(json.dumps([{"record": record.model_dump(mode="json"), "score": score} for record, score in results])))
    finally:
        runtime.close()


@workflow_app.command("run")
def workflow_run(
    path: Annotated[Path, typer.Argument(help="Workflow YAML or JSON file.")],
    online: Annotated[bool, typer.Option("--online")] = False,
    approved: Annotated[bool, typer.Option("--approved")] = False,
) -> None:
    async def _run() -> None:
        runtime = OmegaRuntime.create(online=online, approved=approved)
        try:
            workflow = load_workflow(path)
            result = await run_workflow(runtime, workflow)
            console.print(JSON(json.dumps(result)))
        finally:
            runtime.close()

    asyncio.run(_run())
