from __future__ import annotations

from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class OCRPlugin(Plugin):
    name = "ocr"
    description = "Extract text from images with pytesseract when installed."
    actions = {
        "image_to_text": "Run OCR on an image.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action != "image_to_text":
            return self.unknown_action(action)
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return PluginResult(plugin=self.name, action=action, ok=False, error="Pillow and pytesseract are required for OCR.")
        path = context.permissions.resolve_path(arguments["path"])
        text = pytesseract.image_to_string(Image.open(path))
        return PluginResult(plugin=self.name, action=action, ok=True, data={"text": text})
