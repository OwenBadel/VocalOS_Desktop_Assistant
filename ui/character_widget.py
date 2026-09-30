"""
Personaje Animado Flotante de Escritorio para Ari (Ari-VoiceCommand en Español).
Ventana flotante transparente, arrastrable, con bocadillo de diálogo,
animación de fotogramas (idle/sit) y menú contextual en español.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QCursor, QAction
from PyQt6.QtWidgets import QWidget, QMenu, QApplication

from .speech_bubble import SpeechBubble


class CharacterWidget(QWidget):
    # Señales para comunicación desacoplada con el motor de voz
    request_listen_signal = pyqtSignal()
    command_triggered_signal = pyqtSignal(str)

    def __init__(self, assets_dir: Optional[Path] = None):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.assets_dir = assets_dir or Path(__file__).resolve().parent.parent / "assets" / "character"
        
        # Cargar fotogramas de animación
        self.idle_frames: List[QPixmap] = []
        self.sit_frames: List[QPixmap] = []
        self._load_sprites()

        self.current_frames = self.idle_frames
        self.current_frame_idx = 0
        self.current_pixmap: Optional[QPixmap] = self.current_frames[0] if self.current_frames else None

        # Posicionamiento inicial en la esquina inferior derecha del escritorio
        self.character_size = 140
        self.resize(self.character_size, self.character_size)
        self._position_on_screen()

        # Bocadillo de diálogo
        self.bubble = SpeechBubble()
        self._update_bubble_position()

        # Temporizador de animación de sprites (~10 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._next_frame)
        self.anim_timer.start(110)

        # Variables para arrastre con el ratón
        self.dragging = False
        self.drag_position = QPoint()

        # Estado del personaje
        self.state = "idle"  # idle, listening, thinking, speaking

    def _load_sprites(self):
        """Carga los fotogramas PNG desde assets."""
        for i in range(1, 11):
            idle_p = self.assets_dir / f"idle{i}.png"
            if idle_p.exists():
                pix = QPixmap(str(idle_p))
                self.idle_frames.append(pix)
            
            sit_p = self.assets_dir / f"sit{i}.png"
            if sit_p.exists():
                pix = QPixmap(str(sit_p))
                self.sit_frames.append(pix)

        if not self.idle_frames:
            # Fallback si no hay imágenes: crear un pixmap transparente
            fallback = QPixmap(128, 128)
            fallback.fill(Qt.GlobalColor.transparent)
            self.idle_frames.append(fallback)

    def _position_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            # Ubicar 60px sobre la barra de tareas y 80px del borde derecho
            x = geom.width() - self.width() - 80
            y = geom.height() - self.height() - 40
            self.move(x, y)

    def _update_bubble_position(self):
        if hasattr(self, "bubble") and self.bubble:
            bx = self.x() + (self.width() - self.bubble.width()) // 2
            by = self.y() - self.bubble.height() - 8
            self.bubble.move(bx, by)

    def _next_frame(self):
        if not self.current_frames:
            return
        self.current_frame_idx = (self.current_frame_idx + 1) % len(self.current_frames)
        self.current_pixmap = self.current_frames[self.current_frame_idx]
        self.update()

    def set_mood(self, mood: str):
        """Cambia el conjunto de animación (idle, sit, etc.)."""
        self.state = mood
        if mood == "sit" and self.sit_frames:
            self.current_frames = self.sit_frames
        else:
            self.current_frames = self.idle_frames
        self.current_frame_idx = 0

    def say(self, text: str, duration_ms: int = 5000):
        """Muestra el bocadillo de diálogo sobre la cabeza de Ari."""
        self._update_bubble_position()
        self.bubble.show_message(text, duration_ms)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.current_pixmap and not self.current_pixmap.isNull():
            # Escalar proporcionalmente al tamaño del widget
            scaled = self.current_pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # Centrar en el widget
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # Si está escuchando, dibujar un halo brillante sutil
        if self.state == "listening":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Qt.GlobalColor.cyan)
            painter.setOpacity(0.3)
            painter.drawEllipse(10, 10, self.width() - 20, self.height() - 20)

    # Arrastre con el ratón
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self._update_bubble_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.dragging:
                # Clic sin arrastre: alternar escucha
                self.request_listen_signal.emit()
            self.dragging = False
            self._update_bubble_position()

    def contextMenuEvent(self, event):
        """Menú contextual con clic derecho en español."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 240);
                color: #f8fafc;
                border: 1px solid #06b6d4;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(6, 182, 212, 0.25);
                color: #22d3ee;
            }
        """)

        act_listen = QAction("🎙️ Escuchar orden ahora", self)
        act_listen.triggered.connect(lambda: self.request_listen_signal.emit())
        menu.addAction(act_listen)

        act_vlc = QAction("🎬 Reproducir Owari no Seraph en VLC", self)
        act_vlc.triggered.connect(lambda: self.command_triggered_signal.emit("reproduceme en vlc el anime owari no seraph"))
        menu.addAction(act_vlc)

        act_anime_folder = QAction("📁 Abrir carpeta de Anime (D:\\Anime)", self)
        act_anime_folder.triggered.connect(lambda: self.command_triggered_signal.emit("abre la carpeta anime"))
        menu.addAction(act_anime_folder)

        menu.addSeparator()

        act_sit = QAction("🧘 Cambiar pose (Sentada / De pie)", self)
        act_sit.triggered.connect(lambda: self.set_mood("sit" if self.state != "sit" else "idle"))
        menu.addAction(act_sit)

        menu.addSeparator()

        act_exit = QAction("❌ Salir de Ari", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_exit)

        menu.exec(QCursor.pos())

    def closeEvent(self, event):
        if hasattr(self, "bubble") and self.bubble:
            self.bubble.close()
        super().closeEvent(event)
