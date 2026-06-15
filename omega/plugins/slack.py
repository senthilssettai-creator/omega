from __future__ import annotations

from typing import Any

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class SlackPlugin(Plugin):
    name = "slack"
    description = "Send Slack notifications and query channels using webhooks or bot tokens."
    actions = {
        "post_message": "Post a message to a Slack webhook or channel.",
        "list_channels": "List Slack channels using a bot token.",
        "fetch_messages": "Fetch recent messages from a Slack channel.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "post_message":
            url = arguments.get("webhook_url") or context.settings.slack_webhook_url
            if not url:
                return PluginResult(plugin=self.name, action=action, ok=False, error="SLACK_WEBHOOK_URL or webhook_url is required.")
            text = str(arguments.get("text", ""))
            if not text:
                return PluginResult(plugin=self.name, action=action, ok=False, error="Message text is required.")
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, json={"text": text})
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=response.status_code < 300,
                data={"status_code": response.status_code, "text": response.text.strip()},
                error=None if response.status_code < 300 else response.text[:1000],
            )

        token = arguments.get("token") or context.settings.slack_bot_token
        if not token:
            return PluginResult(plugin=self.name, action=action, ok=False, error="SLACK_BOT_TOKEN or token is required for this Slack action.")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}
        if action == "list_channels":
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get("https://slack.com/api/conversations.list", headers=headers, params={"limit": 50})
            data = response.json()
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=data.get("ok", False),
                data=[{"id": channel.get("id"), "name": channel.get("name"), "is_private": channel.get("is_private")} for channel in data.get("channels", [])],
                error=None if data.get("ok", False) else data.get("error", "Slack API error."),
            )

        if action == "fetch_messages":
            channel = arguments.get("channel")
            if not channel:
                return PluginResult(plugin=self.name, action=action, ok=False, error="channel is required.")
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://slack.com/api/conversations.history",
                    headers=headers,
                    params={"channel": str(channel), "limit": int(arguments.get("limit", 20))},
                )
            data = response.json()
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=data.get("ok", False),
                data=data.get("messages", []),
                error=None if data.get("ok", False) else data.get("error", "Slack API error."),
            )

        return self.unknown_action(action)
