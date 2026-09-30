"""
Oyente de Voz en Segundo Plano (Continuous Background Listener).
Captura audio del micrófono de bajo consumo mediante sounddevice y detección VAD
(Voice Activity Detection) por energía RMS. Ideal para operar sin interacción manual.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import collections
import time
import numpy as np
import sounddevice as sd
from typing import Callable, Optional


class VoiceListener:
    @staticmethod
    def list_input_devices() -> list[dict]:
        """Retorna lista de micrófonos detectados en el sistema."""
        devices = []
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append({
                        "index": idx,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"]
                    })
        except Exception as e:
            print(f"[VoiceListener] Error listando dispositivos: {e}")
        return devices

    @staticmethod
    def resolve_device(target: Optional[str | int] = "nvidia") -> tuple[Optional[int], str]:
        """Resuelve el índice y nombre del dispositivo de audio según patrón o índice."""
        devices = VoiceListener.list_input_devices()
        if not devices:
            return None, "Dispositivo predeterminado del sistema"

        # Si target es un entero
        if isinstance(target, int):
            for d in devices:
                if d["index"] == target:
                    return d["index"], d["name"]

        # Si target es string (e.g. "nvidia" o "broadcast")
        if isinstance(target, str) and target.strip():
            query = target.lower().strip()
            for d in devices:
                if query in d["name"].lower():
                    return d["index"], d["name"]

        # Fallback a NVIDIA si no se especificó o no se encontró
        for d in devices:
            if "nvidia" in d["name"].lower():
                return d["index"], d["name"]

        # Fallback al predeterminado del sistema
        try:
            default_in = sd.default.device[0]
            if default_in is not None and default_in >= 0:
                for d in devices:
                    if d["index"] == default_in:
                        return d["index"], d["name"]
        except Exception:
            pass

        return (devices[0]["index"], devices[0]["name"]) if devices else (None, "Desconocido")

    def __init__(
        self,
        sample_rate: int = 16000,
        energy_threshold: int = 900,
        silence_duration_seconds: float = 0.9,
        max_phrase_seconds: float = 12.0,
        device_name_or_index: Optional[str | int] = "nvidia",
        on_phrase_callback: Optional[Callable[[np.ndarray], None]] = None
    ):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration_seconds
        self.max_phrase_seconds = max_phrase_seconds
        self.on_phrase_callback = on_phrase_callback
        
        self.device_index, self.device_name = self.resolve_device(device_name_or_index)
        self.is_running = False
        self.stream: Optional[sd.InputStream] = None

    def start(self):
        """Inicia el bucle de escucha continuo en el hilo actual o desacoplado."""
        self.is_running = True
        block_size = 1024  # ~64ms por bloque a 16kHz
        
        # Buffer circular para conservar los primeros 0.4s previos a superar el umbral
        pre_buffer_blocks = int(0.4 * self.sample_rate / block_size)
        pre_buffer = collections.deque(maxlen=pre_buffer_blocks)
        
        active_phrase = []
        is_speaking = False
        silence_start_time = None

        print(f"[VoiceListener] 🎙️ Escuchando con micrófono '{self.device_name}' (ID: {self.device_index}) a 16 kHz (Umbral RMS: {self.energy_threshold})...")

        with sd.InputStream(
            device=self.device_index,
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=block_size
        ) as stream:
            self.stream = stream
            while self.is_running:
                data, overflowed = stream.read(block_size)
                samples = data.flatten()
                
                # Calcular RMS
                rms = int(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
                now = time.time()

                if not is_speaking:
                    pre_buffer.append(samples)
                    if rms > self.energy_threshold:
                        # Comienza a hablar el usuario
                        is_speaking = True
                        active_phrase = list(pre_buffer)
                        active_phrase.append(samples)
                        silence_start_time = None
                else:
                    active_phrase.append(samples)
                    total_seconds = (len(active_phrase) * block_size) / self.sample_rate

                    if rms < self.energy_threshold:
                        if silence_start_time is None:
                            silence_start_time = now
                        elif (now - silence_start_time) >= self.silence_duration:
                            # Fin de la frase detectado por silencio
                            audio_array = np.concatenate(active_phrase)
                            self._emit_phrase(audio_array)
                            is_speaking = False
                            active_phrase = []
                            pre_buffer.clear()
                            silence_start_time = None
                    else:
                        silence_start_time = None

                    # Limitar duración máxima de frase
                    if total_seconds >= self.max_phrase_seconds:
                        audio_array = np.concatenate(active_phrase)
                        self._emit_phrase(audio_array)
                        is_speaking = False
                        active_phrase = []
                        pre_buffer.clear()
                        silence_start_time = None

    def _emit_phrase(self, audio: np.ndarray):
        duration = len(audio) / self.sample_rate
        if duration >= 0.6:  # Descartar chasquidos breves menores a 600ms
            if self.on_phrase_callback:
                self.on_phrase_callback(audio)

    def stop(self):
        """Detiene el oyente en segundo plano."""
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
