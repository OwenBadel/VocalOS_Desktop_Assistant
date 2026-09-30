"""
Herramienta CLI de Calibración y Enrolamiento de Voz para Owen Badel Hooker.
Permite entrenar la huella acústica directamente desde el micrófono o desde un archivo de audio.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np
import sounddevice as sd

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.voice_biometrics import VoiceBiometrics


def record_sample(seconds: int = 4, sample_rate: int = 16000) -> np.ndarray:
    print(f"\n[Grabando] Habla durante {seconds} segundos...")
    recording = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    for s in range(seconds, 0, -1):
        print(f" -> Tiempo restante: {s}s...", end="\r", flush=True)
        time.sleep(1)
    sd.wait()
    print("\n[Listo] Muestra capturada.")
    return recording.flatten()


def main():
    print("=" * 60)
    print("🎙️  VOCALOS — CALIBRACIÓN Y ENROLAMIENTO BIOMÉTRICO")
    print("Titular: Owen Badel Hooker")
    print("=" * 60)

    bio = VoiceBiometrics()
    user_name = "Owen Badel Hooker"

    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            audio_path = sys.argv[idx + 1]
            import imageio_ffmpeg
            import subprocess
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [ffmpeg_exe, "-y", "-i", audio_path, "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw, _ = proc.communicate()
            audio = np.frombuffer(raw, dtype=np.int16)
            
            sample_len = 16000 * 3
            samples = []
            for start in range(0, len(audio) - sample_len, 16000 * 4):
                chunk = audio[start:start + sample_len]
                samples.append(bio.extract_features(chunk))
            
            bio.enroll(user_name, samples, threshold=0.72)
            print(f"✅ Enrolamiento completado con éxito a partir de archivo: {len(samples)} muestras.")
            return

    print("\nVamos a calibrar tu voz con 3 muestras habladas desde el micrófono.")
    print("Frase recomendada: 'VocalOS activa el sistema y reproduce anime en VLC'")
    input("Presiona ENTER para iniciar la Muestra 1...")

    s1 = record_sample(4)
    input("Presiona ENTER para iniciar la Muestra 2...")
    s2 = record_sample(4)
    input("Presiona ENTER para iniciar la Muestra 3...")
    s3 = record_sample(4)

    samples = [
        bio.extract_features(s1),
        bio.extract_features(s2),
        bio.extract_features(s3)
    ]

    bio.enroll(user_name, samples, threshold=0.72)
    print("\n🎉 ¡Huella vocal calibrada y sellada exitosamente para Owen Badel Hooker!")
    print("Ya puedes ejecutar 'python vocalos_daemon.py' y hablarle a tu equipo desde la cama.")


if __name__ == "__main__":
    main()
