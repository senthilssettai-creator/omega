from __future__ import annotations

from typing import Any

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class YouTubePlugin(Plugin):
    name = "youtube"
    description = "Analyze YouTube metadata through yt-dlp or public oEmbed."
    actions = {
        "metadata": "Fetch video metadata.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action != "metadata":
            return self.unknown_action(action)
        url = str(arguments["url"])
        try:
            import yt_dlp
        except ImportError:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get("https://www.youtube.com/oembed", params={"url": url, "format": "json"})
            return PluginResult(
                plugin=self.name,
                action=action,
                ok=response.status_code < 400,
                data=response.json() if response.status_code < 400 else None,
                error=None if response.status_code < 400 else response.text[:1000],
            )
        options = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)
        keep = ["id", "title", "channel", "duration", "view_count", "upload_date", "description", "webpage_url"]
        return PluginResult(plugin=self.name, action=action, ok=True, data={key: info.get(key) for key in keep})
