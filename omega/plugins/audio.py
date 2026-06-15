from __future__ import annotations

import wave
from typing import Any

from omega.plugins.base import Plugin, PluginContext
from omega.schema import PluginResult


class AudioPlugin(Plugin):
    name = "audio"
    description = "Inspect WAV files and run optional local speech-to-text or text-to-speech adapters."
    actions = {
        "wav_info": "Inspect WAV audio metadata.",
        "speech_to_text": "Transcribe audio with speech_recognition when installed.",
        "text_to_speech": "Generate speech with pyttsx3 when installed.",
    }

    async def call(self, action: str, arguments: dict[str, Any], context: PluginContext) -> PluginResult:
        if action == "wav_info":
            path = context.permissions.resolve_path(arguments["path"])
            with wave.open(str(path), "rb") as wav:
                data = {
                    "channels": wav.getnchannels(),
                    "sample_width": wav.getsampwidth(),
                    "frame_rate": wav.getframerate(),
                    "frames": wav.getnframes(),
                    "duration_seconds": wav.getnframes() / float(wav.getframerate()),
                }
            return PluginResult(plugin=self.name, action=action, ok=True, data=data)
        if action == "speech_to_text":
            try:
                import speech_recognition as sr
            except ImportError:
                return PluginResult(plugin=self.name, action=action, ok=False, error="speech_recognition is not installed.")
            path = context.permissions.resolve_path(arguments["path"])
            recognizer = sr.Recognizer()
            with sr.AudioFile(str(path)) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return PluginResult(plugin=self.name, action=action, ok=True, data={"text": text})
        if action == "text_to_speech":
            try:
                import pyttsx3
            except ImportError:
                return PluginResult(plugin=self.name, action=action, ok=False, error="pyttsx3 is not installed.")
            output = context.permissions.resolve_path(arguments["path"])
            engine = pyttsx3.init()
            engine.save_to_file(str(arguments["text"]), str(output))
            engine.runAndWait()
            return PluginResult(plugin=self.name, action=action, ok=True, data={"path": str(output)})
        return self.unknown_action(action)
