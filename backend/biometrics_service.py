"""
Servicio de Biometría Vocal y Verificación de Locutor (Speaker Verification).
Permite enrolar el perfil de voz del propietario (Owen Badel Hooker) y validar
biométricamente las peticiones de audio entrantes antes de autorizar comandos.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import signal, fft
from scipy.spatial.distance import cosine


class VoiceBiometricsService:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.data_dir / "voice_profile.json"
        
        # Umbral mínimo de similitud coseno para autorizar ejecución (0.0 a 1.0)
        self.similarity_threshold = 0.78
        self.profile: Optional[Dict] = None
        self.load_profile()

    def load_profile(self) -> Optional[Dict]:
        """Carga el perfil de voz guardado si existe."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.profile = json.load(f)
                return self.profile
            except Exception as e:
                print(f"[Biometrics] Error al cargar perfil: {e}")
        return None

    def extract_features(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extrae un vector acústico representativo (64 dimensiones) a partir de la señal de audio.
        Aplica filtro de pre-énfasis, ventana de Hamming, FFT de potencia y bancos espectrales.
        """
        if len(audio_data) == 0:
            return np.zeros(64, dtype=np.float32)
        
        # Asegurar tipo flotante normalizado entre -1.0 y 1.0
        samples = audio_data.astype(np.float32)
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val

        # 1. Filtro de pre-énfasis para atenuar frecuencias bajas y resaltar formantes vocales
        pre_emphasis = 0.97
        emphasized = np.append(samples[0], samples[1:] - pre_emphasis * samples[:-1])

        # 2. Ventana de análisis Hamming
        window = signal.windows.hamming(len(emphasized))
        windowed = emphasized * window

        # 3. Transformada Rápida de Fourier (FFT) para obtener espectro de potencia
        spectrum = np.abs(fft.rfft(windowed))
        power_spectrum = (spectrum ** 2) / (len(windowed) + 1e-10)

        # 4. Agrupación en 64 bandas espectrales logarítmicas
        num_bands = 64
        step = max(1, len(power_spectrum) // num_bands)
        bands = []
        for i in range(num_bands):
            start = i * step
            end = min(len(power_spectrum), (i + 1) * step)
            if start < end:
                bands.append(np.mean(power_spectrum[start:end]))
            else:
                bands.append(0.0)

        # 5. Transformación logarítmica y centrado medio (Zero-centering para eliminar sesgo de suelo)
        log_bands = np.log10(np.array(bands, dtype=np.float32) + 1e-9)
        centered = log_bands - np.mean(log_bands)
        norm = np.linalg.norm(centered)
        if norm > 0:
            feature_vector = centered / norm
        else:
            feature_vector = centered

        return feature_vector

    def enroll_profile(self, user_name: str, sample_vectors: List[np.ndarray], threshold: float = 0.78) -> Dict:
        """
        Registra el perfil de voz calculando el centroide (vector medio)
        a partir de 3 o más muestras acústicas de calibración.
        """
        if not sample_vectors:
            raise ValueError("Se requiere al menos una muestra acústica para el enrolamiento.")

        # Calcular vector medio representativo (centroide de la huella)
        centroid = np.mean(sample_vectors, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        self.similarity_threshold = threshold
        self.profile = {
            "user_name": user_name,
            "threshold": threshold,
            "sample_count": len(sample_vectors),
            "voiceprint": centroid.tolist(),
            "enrolled_at": str(np.datetime64("now"))
        }

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=2, ensure_ascii=False)

        print(f"[Biometrics] Perfil enrolado exitosamente para: {user_name} con umbral {threshold}")
        return self.profile

    def verify_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[bool, float, str]:
        """
        Compara el vector acústico del audio entrante contra la huella registrada.
        Retorna (autorizado: bool, confianza: float, mensaje: str).
        """
        if not self.profile or "voiceprint" not in self.profile:
            # Si no hay perfil entrenado, se opera en modo desarrollo/alerta
            return False, 0.0, "No existe ningún perfil biométrico registrado. Por favor entrena tu voz."

        target_voiceprint = np.array(self.profile["voiceprint"], dtype=np.float32)
        test_features = self.extract_features(audio_data, sample_rate)

        # Similitud Coseno: 1 - cosine_distance
        dist = cosine(target_voiceprint, test_features)
        similarity = float(max(0.0, 1.0 - dist))

        threshold = self.profile.get("threshold", self.similarity_threshold)
        is_verified = similarity >= threshold

        user_name = self.profile.get("user_name", "Usuario")
        if is_verified:
            msg = f"Identidad verificada: {user_name} (Confianza: {similarity*100:.1f}%)"
        else:
            msg = f"Acceso denegado: Voz no autorizada (Similitud: {similarity*100:.1f}% < Umbral: {threshold*100:.1f}%)"

        return is_verified, similarity, msg

    def get_status(self) -> Dict:
        """Retorna el estado actual del motor biométrico."""
        if not self.profile:
            return {
                "enrolled": False,
                "user_name": None,
                "threshold": self.similarity_threshold,
                "status": "SIN_PERFIL"
            }
        return {
            "enrolled": True,
            "user_name": self.profile.get("user_name"),
            "threshold": self.profile.get("threshold", self.similarity_threshold),
            "enrolled_at": self.profile.get("enrolled_at"),
            "status": "ACTIVO_Y_VERIFICANDO"
        }
