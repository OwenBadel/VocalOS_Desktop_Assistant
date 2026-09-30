"""
Daemon de Segundo Plano de VocalOS (Background Voice OS Assistant).
Opera silenciosamente en segundo plano sin interfaces web ni navegadores.
Escucha continuamente desde el micrófono, valida la huella vocal de Owen Badel Hooker,
transcribe con Faster-Whisper y ejecuta la orden (reproducir anime en VLC, abrir carpetas,
juegos como R.E.P.O. o PEAK, terminal, etc.).
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import os
import sys
import threading
import time
from pathlib import Path

# Añadir raíz al sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.voice_biometrics import VoiceBiometrics
from core.speech_transcriber import SpeechTranscriber
from core.command_dispatcher import CommandDispatcher
from core.media_searcher import MediaSearcher
from core.voice_listener import VoiceListener


class VocalOSDaemon:
    def __init__(self, energy_threshold: int = 850, model_size: str = "base"):
        print("=" * 65)
        print("🎙️  VOCALOS DAEMON — ASISTENTE OPERATIVO EN SEGUNDO PLANO")
        print("🛡️  Zero-Trust Acústico: Autorización exclusiva para Owen Badel Hooker")
        print("=" * 65)

        self.biometrics = VoiceBiometrics()
        self.transcriber = SpeechTranscriber.get_instance(model_size)
        self.media_searcher = MediaSearcher()
        self.dispatcher = CommandDispatcher(self.media_searcher)
        
        self.listener = VoiceListener(
            energy_threshold=energy_threshold,
            silence_duration_seconds=0.85,
            on_phrase_callback=self.on_voice_detected
        )
        self.is_processing = False

    def on_voice_detected(self, audio_data):
        """Callback invocado por el listener cuando se detecta una frase hablada."""
        if self.is_processing:
            return

        self.is_processing = True
        try:
            duration = len(audio_data) / 16000
            print(f"\n[Oyente] Audio capturado ({duration:.2f}s). Verificando biometría...")

            # 1. Filtro Biométrico de Locutor
            verified, conf, msg = self.biometrics.verify(audio_data)
            if not verified:
                print(f"[Seguridad] 🚫 {msg}. Petición ignorada.")
                return

            print(f"[Seguridad] ✅ {msg}.")

            # 2. Transcripción con Faster-Whisper
            print("[Whisper] Transcribiendo orden vocal...")
            text = self.transcriber.transcribe(audio_data)
            if not text:
                print("[Whisper] Audio sin contenido inteligible.")
                return

            print(f"[Whisper] Transcripción: \"{text}\"")

            # 3. Despacho y Ejecución de la Acción
            result = self.dispatcher.dispatch(text)
            action = result.get("action")
            print(f"[Ejecución] Acción completada: {action}")
            if "result" in result and isinstance(result["result"], dict):
                msg_out = result["result"].get("message") or result["result"].get("error")
                if msg_out:
                    print(f" -> {msg_out}")

        except Exception as e:
            print(f"[Error Daemon] {e}")
        finally:
            self.is_processing = False

    def start(self, use_tray: bool = False):
        """Inicia el servicio en segundo plano."""
        if use_tray:
            self._start_with_system_tray()
        else:
            self._start_console()

    def _start_console(self):
        print("\n[VocalOS Daemon] En ejecución continua en segundo plano.")
        print("[Instrucción] Habla al micrófono desde la cama (Ej: 'Reprodúceme en VLC el anime Owari no Seraph').")
        print("[Control] Presiona Ctrl+C para finalizar.\n")
        try:
            self.listener.start()
        except KeyboardInterrupt:
            print("\n[VocalOS Daemon] Deteniendo servicio...")
            self.listener.stop()

    def _start_with_system_tray(self):
        """Inicia el daemon con icono en la bandeja de sistema de Windows (System Tray)."""
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Generar icono dinámico cian de 64x64
            img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((8, 8, 56, 56), fill=(6, 182, 212, 255), outline=(34, 211, 238, 255), width=2)
            draw.ellipse((22, 22, 42, 42), fill=(16, 19, 29, 255))

            def on_exit(icon, item):
                self.listener.stop()
                icon.stop()

            menu = pystray.Menu(
                pystray.MenuItem("VocalOS: Escuchando a Owen", None, enabled=False),
                pystray.MenuItem("Salir", on_exit)
            )

            icon = pystray.Icon("VocalOS", img, "VocalOS Desktop Assistant", menu)

            # Iniciar hilo del listener
            listener_thread = threading.Thread(target=self.listener.start, daemon=True)
            listener_thread.start()

            print("\n[VocalOS Daemon] Corriendo en la Bandeja del Sistema (System Tray).")
            icon.run()

        except Exception as e:
            print(f"[Aviso] No se pudo iniciar bandeja del sistema: {e}. Iniciando en consola.")
            self._start_console()


if __name__ == "__main__":
    tray_mode = "--tray" in sys.argv
    # Umbral de energía configurable vía argumento
    threshold = 850
    for arg in sys.argv:
        if arg.startswith("--threshold="):
            threshold = int(arg.split("=")[1])

    daemon = VocalOSDaemon(energy_threshold=threshold)
    daemon.start(use_tray=tray_mode)
