"""
Transcriptor Local Ultrarrápido con Faster-Whisper.
Ejecuta inferencia local con cuantización int8 en CPU o aceleración disponible.
100% offline y sin necesidad de internet.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel


class SpeechTranscriber:
    _instance: Optional[SpeechTranscriber] = None

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        print(f"[Transcriber] Cargando modelo Whisper '{model_size}' (CPU int8)...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("[Transcriber] Modelo Whisper listo para transcripción instantánea.")

    @classmethod
    def get_instance(cls, model_size: str = "base") -> SpeechTranscriber:
        if cls._instance is None:
            cls._instance = cls(model_size)
        return cls._instance

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe una señal de audio (int16 o float32) a texto en español.
        """
        if len(audio_data) == 0:
            return ""

        # Normalizar a float32 entre -1.0 y 1.0
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_float = audio_data.astype(np.float32)
            max_val = np.max(np.abs(audio_float))
            if max_val > 0:
                audio_float = audio_float / max_val

        segments, info = self.model.transcribe(
            audio_float,
            language="es",
            beam_size=3,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )

        full_text = " ".join(s.text for s in segments).strip()
        return full_text
