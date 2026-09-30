"""
Motor de Síntesis de Voz (Text-to-Speech) en Español para Ari.
Utiliza Microsoft Edge Neural TTS ('es-ES-ElviraNeural') y reproducción directa
mediante sounddevice y soundfile para una voz natural en tiempo real.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import asyncio
import io
import threading
from typing import Optional
import edge_tts
import soundfile as sf
import sounddevice as sd


class TTSEngine:
    def __init__(self, voice: str = "es-ES-ElviraNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.is_speaking = False
        self._lock = threading.Lock()

    def speak(self, text: str, blocking: bool = False):
        """
        Sintetiza y reproduce el texto en español en segundo plano o síncrono.
        """
        if not text or not text.strip():
            return

        def _worker():
            with self._lock:
                self.is_speaking = True
                try:
                    asyncio.run(self._synthesize_and_play(text))
                except Exception as e:
                    print(f"[TTS Error] {e}")
                finally:
                    self.is_speaking = False

        if blocking:
            _worker()
        else:
            threading.Thread(target=_worker, daemon=True).start()

    async def _synthesize_and_play(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
        audio_stream = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream += chunk["data"]

        if not audio_stream:
            return

        # Leer audio en memoria y reproducir
        data, sample_rate = sf.read(io.BytesIO(audio_stream))
        sd.play(data, sample_rate)
        sd.wait()
