from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class EmailPlugin(Plugin):
    name = "email"
    description = "Send email through a user-provided SMTP server."
    actions = {
        "send": "Send an email with SMTP credentials supplied at call time.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action != "send":
            return self.unknown_action(action)
        message = EmailMessage()
        message["From"] = str(arguments["from"])
        message["To"] = ", ".join(arguments["to"]) if isinstance(arguments["to"], list) else str(arguments["to"])
        message["Subject"] = str(arguments["subject"])
        message.set_content(str(arguments.get("body", "")))
        host = str(arguments["smtp_host"])
        port = int(arguments.get("smtp_port", 587))
        username = arguments.get("username")
        password = arguments.get("password")
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if bool(arguments.get("starttls", True)):
                smtp.starttls()
            if username and password:
                smtp.login(str(username), str(password))
            smtp.send_message(message)
        return PluginResult(plugin=self.name, action=action, ok=True, data={"sent": True, "to": message["To"]})
