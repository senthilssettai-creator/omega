from __future__ import annotations

from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class BrowserPlugin(Plugin):
    name = "browser"
    description = "Automate web pages with Playwright when browser binaries are installed."
    actions = {
        "extract_text": "Open a page and extract visible text.",
        "screenshot": "Capture a page screenshot.",
        "form_fill": "Fill form fields and optionally click a submit selector.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return PluginResult(plugin=self.name, action=action, ok=False, error="playwright is not installed.")

        url = str(arguments["url"])
        headless = bool(arguments.get("headless", True))
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=headless)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=int(arguments.get("timeout_ms", 30000)))
                if action == "extract_text":
                    text = await page.locator("body").inner_text(timeout=10000)
                    await browser.close()
                    return PluginResult(plugin=self.name, action=action, ok=True, data={"url": url, "text": text})
                if action == "screenshot":
                    output = context.permissions.resolve_path(arguments.get("path", "omega_screenshot.png"))
                    output.parent.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(output), full_page=bool(arguments.get("full_page", True)))
                    await browser.close()
                    return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(output)})
                if action == "form_fill":
                    for selector, value in dict(arguments.get("fields", {})).items():
                        await page.fill(selector, str(value))
                    submit_selector = arguments.get("submit")
                    if submit_selector:
                        await page.click(str(submit_selector))
                        await page.wait_for_load_state("networkidle", timeout=int(arguments.get("timeout_ms", 30000)))
                    text = await page.locator("body").inner_text(timeout=10000)
                    await browser.close()
                    return PluginResult(plugin=self.name, action=action, ok=True, data={"url": page.url, "text": text})
                await browser.close()
        except Exception as exc:
            return PluginResult(plugin=self.name, action=action, ok=False, error=str(exc))
        return self.unknown_action(action)
