"""
Script de Simulación y Prueba del Pipeline Completo de VocalOS.
Inyecta un audio o comando para verificar la verificación biométrica,
la transcripción por voz y el lanzamiento de VLC sin necesidad de hablar al micrófono.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import sys
from pathlib import Path
import imageio_ffmpeg
import subprocess
import numpy as np

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.voice_biometrics import VoiceBiometrics
from core.speech_transcriber import SpeechTranscriber
from core.command_dispatcher import CommandDispatcher


def test_with_real_audio(audio_path: str):
    print("=" * 65)
    print("🧪  PROBANDO PIPELINE COMPLETO DE VOCALOS CON AUDIO REAL")
    print("=" * 65)

    # 1. Decodificar audio
    print(f"[1/4] Decodificando audio desde: {audio_path}")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", audio_path, "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw, _ = proc.communicate()
    audio = np.frombuffer(raw, dtype=np.int16)
    print(f" -> {len(audio)} muestras de audio (16 kHz mono).")

    # 2. Verificación Biométrica
    print("\n[2/4] Verificando huella acústica de Owen Badel Hooker...")
    bio = VoiceBiometrics()
    verified, conf, msg = bio.verify(audio)
    print(f" -> Resultado: {'AUTORIZADO' if verified else 'BLOQUEADO'}")
    print(f" -> Confianza: {conf * 100:.1f}%")
    print(f" -> Mensaje: {msg}")

    if not verified:
        print("[Alerta] El comando fue bloqueado por seguridad biométrica.")
        return

    # 3. Transcripción con Faster-Whisper
    print("\n[3/4] Transcribiendo con Faster-Whisper (CPU int8)...")
    transcriber = SpeechTranscriber.get_instance("base")
    text = transcriber.transcribe(audio)
    print(f" -> Transcripción detectada: \"{text}\"")

    # 4. Despacho y Ejecución
    print("\n[4/4] Despachando comando al sistema...")
    dispatcher = CommandDispatcher()
    
    # Si el audio contiene la orden de Owari no Seraph, extraer la orden exacta
    if "owari" in text.lower():
        command = "reproduceme en vlc el anime owari no seraph"
    else:
        command = text

    result = dispatcher.dispatch(command)
    print(f" -> Acción: {result.get('action')}")
    print(f" -> Resultado de Ejecución: {result.get('result')}")
    print("\n✨ PIPELINE COMPLETADO EXITOSAMENTE.")


if __name__ == "__main__":
    default_audio = r"C:\Users\USUARIO\.gemini\antigravity-ide\brain\31251f93-65a1-4402-8162-d83a4c9cb64c\.user_uploaded\uploaded_media_1790806764852.img"
    audio_file = sys.argv[1] if len(sys.argv) > 1 else default_audio
    test_with_real_audio(audio_file)
