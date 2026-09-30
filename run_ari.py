"""
Ari Desktop Assistant — Entrada Principal (Main Application Entrypoint).
Integra el personaje animado flotante, bocadillo de diálogo, bandeja del sistema,
escucha continua de voz en segundo plano con VAD, biometría Zero-Trust, transcripción
local Whisper, registro de comandos (VLC, Steam, anime, carpetas) y síntesis de voz neuronal.
Todo 100% en español para Owen Badel Hooker.

Autor: Owen Badel Hooker
"""

from __future__ import annotations
import argparse
import os
import sys
import threading
import time
from pathlib import Path

# Configurar codificación UTF-8 en Windows para evitar errores con emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Añadir raíz del proyecto al sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QApplication

from core.voice_biometrics import VoiceBiometrics
from core.speech_transcriber import SpeechTranscriber
from core.media_searcher import MediaSearcher
from core.tts_engine import TTSEngine
from core.voice_listener import VoiceListener
from commands.command_registry import CommandRegistry
from ui.character_widget import CharacterWidget
from ui.tray_icon import AriTrayIcon


class AudioListenerWorker(QObject):
    """
    Trabajador en hilo desacoplado para captura continua de audio sin bloquear la UI de Qt.
    """
    phrase_captured = pyqtSignal(object)  # np.ndarray
    status_changed = pyqtSignal(str)

    def __init__(self, energy_threshold: int = 850):
        super().__init__()
        self.energy_threshold = energy_threshold
        self.listener: VoiceListener | None = None
        self._is_active = True

    @pyqtSlot()
    def start_listening(self):
        self.listener = VoiceListener(
            energy_threshold=self.energy_threshold,
            silence_duration_seconds=0.85,
            on_phrase_callback=self._on_phrase
        )
        self.status_changed.emit("Oyente activo")
        self.listener.start()

    def _on_phrase(self, audio):
        if self._is_active:
            self.phrase_captured.emit(audio)

    def stop(self):
        self._is_active = False
        if self.listener:
            self.listener.stop()


class AriAppController(QObject):
    """
    Controlador central que orquesta la interfaz gráfica, el oyente y la ejecución de órdenes.
    """
    def __init__(self, enable_voice: bool = True, energy_threshold: int = 850):
        super().__init__()
        self.enable_voice = enable_voice
        self.energy_threshold = energy_threshold

        print("\n" + "=" * 65)
        print("🌸 ARI — ASISTENTE OPERATIVO DE ESCRITORIO (EN ESPAÑOL)")
        print("👑 Diseñado exclusivamente para: Owen Badel Hooker")
        print("=" * 65 + "\n")

        # 1. Motores Core
        print("[Ari] Inicializando motores acústicos y biométricos...")
        self.biometrics = VoiceBiometrics()
        self.transcriber = SpeechTranscriber.get_instance("base")
        self.media_searcher = MediaSearcher()
        self.tts = TTSEngine(voice="es-ES-ElviraNeural")
        self.commands = CommandRegistry(self.media_searcher)

        # 2. Componentes de UI
        print("[Ari] Cargando personaje animado y bandeja del sistema...")
        self.character = CharacterWidget()
        self.tray = AriTrayIcon()

        # Conectar señales de la UI
        self.character.request_listen_signal.connect(self.on_manual_listen_requested)
        self.character.command_triggered_signal.connect(self.execute_text_command)

        self.tray.toggle_visibility_signal.connect(self.toggle_character_visibility)
        self.tray.request_listen_signal.connect(self.on_manual_listen_requested)
        self.tray.trigger_command_signal.connect(self.execute_text_command)
        self.tray.toggle_pose_signal.connect(self.toggle_pose)

        # 3. Hilo del Oyente de Voz
        self.listener_thread: QThread | None = None
        self.listener_worker: AudioListenerWorker | None = None
        self.is_processing = False

        if self.enable_voice:
            self._setup_voice_listener()

        # Mostrar personaje e icono de bandeja
        self.character.show()
        self.tray.show()

        # Saludo inicial
        QTimer.singleShot(800, self._initial_greeting)

    def _initial_greeting(self):
        greeting = "¡Hola Owen! Estoy lista para recibir tus órdenes."
        self.character.say(greeting, 4500)
        self.tts.speak(greeting)

    def _setup_voice_listener(self):
        """Inicializa el hilo en segundo plano para escuchar continuamente."""
        self.listener_thread = QThread()
        self.listener_worker = AudioListenerWorker(energy_threshold=self.energy_threshold)
        self.listener_worker.moveToThread(self.listener_thread)

        self.listener_thread.started.connect(self.listener_worker.start_listening)
        self.listener_worker.phrase_captured.connect(self.on_audio_phrase_received)

        self.listener_thread.start()
        print("[Ari] Oyente en segundo plano iniciado exitosamente.")

    @pyqtSlot(object)
    def on_audio_phrase_received(self, audio_data):
        """Procesa una frase de audio capturada por el micrófono."""
        if self.is_processing:
            return

        self.is_processing = True
        self.character.set_mood("idle")
        self.character.say("🎙️ Escuchando orden...", 3000)

        # Procesar en un hilo de trabajo para no congelar la animación del personaje
        threading.Thread(target=self._process_voice_task, args=(audio_data,), daemon=True).start()

    def _process_voice_task(self, audio_data):
        try:
            # 1. Validación Biométrica
            verified, conf, msg = self.biometrics.verify(audio_data)
            if not verified:
                print(f"[Seguridad] 🚫 {msg}. Petición ignorada.")
                QTimer.singleShot(0, lambda: self.character.say("🚫 Voz no reconocida como la de Owen.", 4000))
                return

            print(f"[Seguridad] ✅ {msg}.")

            # 2. Transcripción Faster-Whisper
            QTimer.singleShot(0, lambda: self.character.say("🧠 Procesando orden...", 3000))
            transcript = self.transcriber.transcribe(audio_data)

            if not transcript or not transcript.strip():
                print("[Whisper] No se reconoció contenido inteligible.")
                QTimer.singleShot(0, lambda: self.character.say("No alcancé a entender lo que dijiste.", 3000))
                return

            print(f"[Whisper] Transcripción exitosa: \"{transcript}\"")
            
            # 3. Ejecutar comando
            self.execute_text_command(transcript)

        except Exception as e:
            print(f"[Ari Error] Error en procesamiento de voz: {e}")
            QTimer.singleShot(0, lambda: self.character.say(f"Error: {e}", 4000))
        finally:
            self.is_processing = False

    @pyqtSlot(str)
    def execute_text_command(self, text: str):
        """Ejecuta una orden por texto (vocal o por menú contextual)."""
        print(f"[Ari] Ejecutando orden: '{text}'")
        self.character.say(f"Entendido: {text}", 4000)

        # Ejecutar acción a través del registro
        success, response_tts, action_type = self.commands.handle_command(text)

        # Actualizar bocadillo con la respuesta
        QTimer.singleShot(500, lambda: self.character.say(response_tts, 5000))

        # Síntesis de voz en español
        self.tts.speak(response_tts)

    @pyqtSlot()
    def on_manual_listen_requested(self):
        """Invocado al hacer clic en el personaje o en el menú contextual."""
        self.character.say("¡Dime Owen, te escucho!", 3000)
        self.tts.speak("¡Dime Owen, te escucho!")

    @pyqtSlot()
    def toggle_character_visibility(self):
        """Muestra u oculta la ventana flotante de Ari."""
        if self.character.isVisible():
            self.character.hide()
            if hasattr(self.character, "bubble") and self.character.bubble:
                self.character.bubble.hide()
            self.tray.showMessage(
                "Ari Minimizada",
                "Ari sigue activa en la bandeja del sistema escuchando tus órdenes.",
                self.tray.icon(),
                3000
            )
        else:
            self.character.show()

    @pyqtSlot()
    def toggle_pose(self):
        """Alterna entre pose sentada y de pie."""
        new_state = "sit" if self.character.state != "sit" else "idle"
        self.character.set_mood(new_state)

    def shutdown(self):
        """Detiene de forma limpia todos los hilos y subprocesos."""
        print("[Ari] Deteniendo hilos de ejecución...")
        if self.listener_worker:
            self.listener_worker.stop()
        if self.listener_thread:
            self.listener_thread.quit()
            self.listener_thread.wait(1000)


def main():
    parser = argparse.ArgumentParser(description="Ari Desktop Assistant en Español — Owen Badel Hooker")
    parser.add_argument("--no-voice", action="store_true", help="Desactivar captura por micrófono para pruebas de GUI")
    parser.add_argument("--energy", type=int, default=850, help="Umbral de energía RMS para VAD (def: 850)")
    parser.add_argument("--test-cmd", type=str, default=None, help="Ejecutar un comando de prueba y salir")
    args = parser.parse_args()

    # Si se pide únicamente probar un comando directo por consola
    if args.test_cmd:
        print(f"[Test Ari] Probando comando: '{args.test_cmd}'")
        searcher = MediaSearcher()
        registry = CommandRegistry(searcher)
        success, tts, action = registry.handle_command(args.test_cmd)
        print(f"Resultado: Éxito={success} | Acción={action} | TTS='{tts}'")
        return

    # Iniciar aplicación gráfica con PyQt6
    app = QApplication(sys.argv)
    app.setApplicationName("Ari-VoiceCommand-ES")
    app.setApplicationDisplayName("Ari — Asistente de Escritorio en Español")
    app.setQuitOnLastWindowClosed(False)  # Mantener vivo en bandeja aunque se oculte el widget

    controller = AriAppController(
        enable_voice=not args.no_voice,
        energy_threshold=args.energy
    )

    app.aboutToQuit.connect(controller.shutdown)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
