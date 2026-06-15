from __future__ import annotations

from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PDFPlugin(Plugin):
    name = "pdf"
    description = "Extract PDF text with pypdf and generate simple text PDFs without external services."
    actions = {
        "extract_text": "Extract text from a PDF file.",
        "generate_text_pdf": "Generate a simple one-page text PDF.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "extract_text":
            try:
                from pypdf import PdfReader
            except ImportError:
                return PluginResult(plugin=self.name, action=action, ok=False, error="pypdf is not installed.")
            path = context.permissions.resolve_path(arguments["path"])
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return PluginResult(plugin=self.name, action=action, ok=True, data={"pages": len(reader.pages), "text": text})
        if action == "generate_text_pdf":
            path = context.permissions.resolve_path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            text = _pdf_escape(str(arguments.get("text", ""))[:4000])
            stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
            objects = [
                "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
                "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
                "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
                "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
                f"5 0 obj << /Length {len(stream.encode('latin-1', errors='replace'))} >> stream\n{stream}\nendstream endobj",
            ]
            content = "%PDF-1.4\n"
            offsets = [0]
            for obj in objects:
                offsets.append(len(content.encode("latin-1")))
                content += obj + "\n"
            xref_offset = len(content.encode("latin-1"))
            content += "xref\n0 6\n0000000000 65535 f \n"
            content += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
            content += "trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
            content += f"{xref_offset}\n%%EOF\n"
            path.write_bytes(content.encode("latin-1", errors="replace"))
            return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(path), "bytes": path.stat().st_size})
        return self.unknown_action(action)
