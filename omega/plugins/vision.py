from __future__ import annotations

import base64
import mimetypes
from typing import Any

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class VisionPlugin(Plugin):
    name = "vision"
    description = "Analyze images with OpenRouter multimodal models or return local image metadata."
    actions = {
        "describe_image": "Describe an image using OpenRouter if configured.",
        "metadata": "Read local image metadata with Pillow.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        path = context.permissions.resolve_path(arguments["path"])
        if action == "metadata":
            try:
                from PIL import Image
            except ImportError:
                return PluginResult(plugin=self.name, action=action, ok=False, error="Pillow is not installed.")
            with Image.open(path) as image:
                return PluginResult(plugin=self.name, action=action, ok=True, data={"format": image.format, "size": image.size, "mode": image.mode})
        if action == "describe_image":
            if not context.settings.openrouter_api_key:
                return PluginResult(plugin=self.name, action=action, ok=False, error="OPENROUTER_API_KEY is required for image description.")
            mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            payload = {
                "model": str(arguments.get("model", "qwen/qwen2.5-vl-72b-instruct:free")),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": str(arguments.get("prompt", "Describe this image."))},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
                        ],
                    }
                ],
            }
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{context.settings.openrouter_base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {context.settings.openrouter_api_key}"},
                )
            if response.status_code >= 400:
                return PluginResult(plugin=self.name, action=action, ok=False, error=response.text[:1000])
            data = response.json()
            return PluginResult(plugin=self.name, action=action, ok=True, data={"description": data["choices"][0]["message"]["content"]})
        return self.unknown_action(action)
