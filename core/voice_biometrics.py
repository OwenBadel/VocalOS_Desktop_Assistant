"""
Módulo de Biometría Vocal y Verificación de Locutor para Segundo Plano.
Garantiza que el sistema operativo únicamente ejecute órdenes si el audio
proviene de la huella acústica de Owen Badel Hooker.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import signal, fft
from scipy.spatial.distance import cosine


class VoiceBiometrics:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.data_dir / "voice_profile.json"
        
        self.default_threshold = 0.72
        self.profile: Optional[Dict] = None
        self.load_profile()

    def load_profile(self) -> Optional[Dict]:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.profile = json.load(f)
                return self.profile
            except Exception as e:
                print(f"[Biometrics] Error cargando perfil: {e}")
        return None

    def extract_features(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extrae un vector acústico discriminativo de 64 dimensiones con pre-énfasis
        y zero-centering espectral para eliminar sesgos de volumen y suelo de ruido.
        """
        if len(audio_data) == 0:
            return np.zeros(64, dtype=np.float32)

        samples = audio_data.astype(np.float32)
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val

        # 1. Filtro de pre-énfasis (alza de formantes vocales)
        pre_emphasis = 0.97
        emphasized = np.append(samples[0], samples[1:] - pre_emphasis * samples[:-1])

        # 2. Ventana de Hamming
        window = signal.windows.hamming(len(emphasized))
        windowed = emphasized * window

        # 3. FFT de potencia
        spectrum = np.abs(fft.rfft(windowed))
        power = (spectrum ** 2) / (len(windowed) + 1e-10)

        # 4. Agrupación en 64 bandas espectrales
        num_bands = 64
        step = max(1, len(power) // num_bands)
        bands = []
        for i in range(num_bands):
            start = i * step
            end = min(len(power), (i + 1) * step)
            if start < end:
                bands.append(np.mean(power[start:end]))
            else:
                bands.append(0.0)

        # 5. Escala logarítmica y Zero-Centering
        log_bands = np.log10(np.array(bands, dtype=np.float32) + 1e-9)
        centered = log_bands - np.mean(log_bands)
        norm = np.linalg.norm(centered)
        
        return centered / norm if norm > 0 else centered

    def enroll(self, user_name: str, sample_vectors: List[np.ndarray], threshold: float = 0.72) -> Dict:
        """Sella la huella acústica calculando el centroide representativo."""
        centroid = np.mean(sample_vectors, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        self.profile = {
            "user_name": user_name,
            "threshold": threshold,
            "sample_count": len(sample_vectors),
            "voiceprint": centroid.tolist()
        }

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=2, ensure_ascii=False)

        print(f"[Biometrics] Perfil guardado para {user_name} con umbral {threshold * 100}%.")
        return self.profile

    def verify(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[bool, float, str]:
        """Compara el audio con la huella registrada."""
        if not self.profile or "voiceprint" not in self.profile:
            return True, 1.0, "Modo abierto: sin perfil registrado."

        target = np.array(self.profile["voiceprint"], dtype=np.float32)
        test_feat = self.extract_features(audio_data, sample_rate)

        dist = cosine(target, test_feat)
        similarity = float(max(0.0, 1.0 - dist))
        threshold = self.profile.get("threshold", self.default_threshold)

        is_verified = similarity >= threshold
        user = self.profile.get("user_name", "Owen Badel Hooker")

        if is_verified:
            msg = f"Voz verificada de {user} (Confianza: {similarity*100:.1f}%)"
        else:
            msg = f"Voz no autorizada (Similitud: {similarity*100:.1f}% < {threshold*100:.1f}%)"

        return is_verified, similarity, msg
