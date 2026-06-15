from __future__ import annotations

from omega.plugins.api import APIPlugin
from omega.plugins.audio import AudioPlugin
from omega.plugins.browser import BrowserPlugin
from omega.plugins.calendar import CalendarPlugin
from omega.plugins.database import DatabasePlugin
from omega.plugins.docker import DockerPlugin
from omega.plugins.email import EmailPlugin
from omega.plugins.filesystem import FilesystemPlugin
from omega.plugins.git import GitPlugin
from omega.plugins.mcp import MCPPlugin
from omega.plugins.notes import NotesPlugin
from omega.plugins.ocr import OCRPlugin
from omega.plugins.pdf import PDFPlugin
from omega.plugins.rag import RAGPlugin
from omega.plugins.search import SearchPlugin
from omega.plugins.spreadsheet import SpreadsheetPlugin
from omega.plugins.terminal import TerminalPlugin
from omega.plugins.vision import VisionPlugin
from omega.plugins.youtube import YouTubePlugin
from omega.plugins.github import GitHubPlugin
from omega.plugins.slack import SlackPlugin
from omega.plugins.googledrive import GoogleDrivePlugin


def builtin_plugins():
    return [
        FilesystemPlugin(),
        TerminalPlugin(),
        GitPlugin(),
        GitHubPlugin(),
        DatabasePlugin(),
        DockerPlugin(),
        APIPlugin(),
        BrowserPlugin(),
        SearchPlugin(),
        RAGPlugin(),
        MCPPlugin(),
        NotesPlugin(),
        CalendarPlugin(),
        EmailPlugin(),
        SpreadsheetPlugin(),
        PDFPlugin(),
        OCRPlugin(),
        VisionPlugin(),
        AudioPlugin(),
        YouTubePlugin(),
        SlackPlugin(),
        GoogleDrivePlugin(),
    ]
