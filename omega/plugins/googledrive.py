from __future__ import annotations

from typing import Any
import json

import httpx

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class GoogleDrivePlugin(Plugin):
    name = "google_drive"
    description = "Access Google Drive files and folders with OAuth credentials or API keys."
    actions = {
        "list_files": "List files in a Google Drive folder.",
        "download_file": "Download a file from Google Drive by ID.",
        "upload_file": "Upload a file to Google Drive.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        token = arguments.get("access_token") or context.settings.google_drive_token
        if not token:
            return PluginResult(plugin=self.name, action=action, ok=False, error="GOOGLE_DRIVE_TOKEN is required.")

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if action == "list_files":
            folder_id = str(arguments.get("folder_id", "root"))
            params = {"q": f"'{folder_id}' in parents and trashed = false", "pageSize": 50, "fields": "files(id,name,mimeType,parents)"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get("https://www.googleapis.com/drive/v3/files", headers=headers, params=params)
            if response.status_code >= 400:
                return PluginResult(plugin=self.name, action=action, ok=False, error=response.text[:1000])
            return PluginResult(plugin=self.name, action=action, ok=True, data=response.json().get("files", []))

        if action == "download_file":
            file_id = arguments.get("file_id")
            if not file_id:
                return PluginResult(plugin=self.name, action=action, ok=False, error="file_id is required.")
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media", headers=headers)
            if response.status_code >= 400:
                return PluginResult(plugin=self.name, action=action, ok=False, error=response.text[:1000])
            path = context.permissions.resolve_path(arguments.get("path", file_id))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
            return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(path)})

        if action == "upload_file":
            file_path = context.permissions.resolve_path(arguments.get("path"))
            if not file_path.exists():
                return PluginResult(plugin=self.name, action=action, ok=False, error=f"Local file not found: {file_path}")
            metadata = {"name": file_path.name, "parents": [arguments.get("folder_id", "root")]} 
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                    headers={"Authorization": f"Bearer {token}"},
                    files={
                        "metadata": (None, json.dumps(metadata), "application/json; charset=UTF-8"),
                        "file": (file_path.name, file_path.read_bytes()),
                    },
                )
            if response.status_code >= 400:
                return PluginResult(plugin=self.name, action=action, ok=False, error=response.text[:1000])
            return PluginResult(plugin=self.name, action=action, ok=True, data=response.json())

        return self.unknown_action(action)
