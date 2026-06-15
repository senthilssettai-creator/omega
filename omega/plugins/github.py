from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class GitHubPlugin(Plugin):
    name = "github"
    description = "Interact with GitHub issues, pull requests, and repositories using CLI or API access."
    actions = {
        "repo_clone": "Clone a GitHub repository into the workspace.",
        "issue_search": "Search issues in a GitHub repository.",
        "pr_list": "List pull requests for a GitHub repository.",
        "pr_view": "Inspect a single pull request by number.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "repo_clone":
            repo = str(arguments["repo"])
            target = context.permissions.resolve_path(arguments.get("path", "."))
            target.mkdir(parents=True, exist_ok=True)
            return await self._run_git(["git", "clone", repo, str(target)])

        if action == "issue_search":
            repo = str(arguments["repo"])
            query = str(arguments.get("query", ""))
            token = context.settings.github_token
            if not token:
                return PluginResult(plugin=self.name, action=action, ok=False, error="GITHUB_TOKEN is required for GitHub API access.")
            return await self._search_issues(repo, query, token)

        if action == "pr_list":
            repo = str(arguments["repo"])
            token = context.settings.github_token
            if not token:
                return PluginResult(plugin=self.name, action=action, ok=False, error="GITHUB_TOKEN is required for GitHub API access.")
            return await self._list_pull_requests(repo, token)

        if action == "pr_view":
            repo = str(arguments["repo"])
            number = int(arguments["number"])
            token = context.settings.github_token
            if not token:
                return PluginResult(plugin=self.name, action=action, ok=False, error="GITHUB_TOKEN is required for GitHub API access.")
            return await self._view_pull_request(repo, number, token)

        return self.unknown_action(action)

    async def _run_git(self, argv: list[str]) -> PluginResult:
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            return PluginResult(plugin=self.name, action="repo_clone", ok=False, error=str(exc))
        stdout, stderr = await process.communicate()
        return PluginResult(
            plugin=self.name,
            action="repo_clone",
            ok=process.returncode == 0,
            data={"stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"), "returncode": process.returncode},
            error=None if process.returncode == 0 else f"git exited with {process.returncode}",
        )

    async def _search_issues(self, repo: str, query: str, token: str) -> PluginResult:
        url = "https://api.github.com/search/issues"
        params = {"q": f"repo:{repo} {query}".strip(), "per_page": 20}
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=headers)
        if response.status_code >= 400:
            return PluginResult(plugin=self.name, action="issue_search", ok=False, error=response.text[:1000])
        results = response.json().get("items", [])
        return PluginResult(plugin=self.name, action="issue_search", ok=True, data=[{"title": item.get("title"), "url": item.get("html_url"), "state": item.get("state"), "number": item.get("number")} for item in results])

    async def _list_pull_requests(self, repo: str, token: str) -> PluginResult:
        url = f"https://api.github.com/repos/{repo}/pulls"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"state": "all", "per_page": 20}, headers=headers)
        if response.status_code >= 400:
            return PluginResult(plugin=self.name, action="pr_list", ok=False, error=response.text[:1000])
        return PluginResult(plugin=self.name, action="pr_list", ok=True, data=response.json())

    async def _view_pull_request(self, repo: str, number: int, token: str) -> PluginResult:
        url = f"https://api.github.com/repos/{repo}/pulls/{number}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            return PluginResult(plugin=self.name, action="pr_view", ok=False, error=response.text[:1000])
        return PluginResult(plugin=self.name, action="pr_view", ok=True, data=response.json())
