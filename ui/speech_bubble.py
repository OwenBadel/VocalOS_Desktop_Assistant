"""
Bocadillo de Diálogo Flotante (SpeechBubble) para Ari.
Muestra mensajes de texto, estado y respuestas en español sobre la cabeza del personaje.
Estilo Glassmorphism translúcido con borde neón cian.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect


class SpeechBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 10, 14, 16)

        self.label = QLabel("...", self)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.label.setStyleSheet("color: #f8fafc; background: transparent;")
        self.layout.addWidget(self.label)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        self.setFixedWidth(240)

    def show_message(self, text: str, duration_ms: int = 5000):
        """Muestra un mensaje y programa su ocultamiento."""
        self.label.setText(text)
        self.adjustSize()
        self.show()
        if duration_ms > 0:
            self.hide_timer.start(duration_ms)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensiones del globo sin la colita
        w = self.width()
        h = self.height() - 10
        radius = 8

        path = QPainterPath()
        # Rectángulo redondeado
        path.addRoundedRect(1, 1, w - 2, h - 2, radius, radius)

        # Colita del bocadillo apuntando hacia abajo
        tail_center = w // 2
        path.moveTo(tail_center - 8, h - 2)
        path.lineTo(tail_center, h + 8)
        path.lineTo(tail_center + 8, h - 2)

        # Relleno oscuro glassmorphic
        painter.setBrush(QBrush(QColor(11, 17, 32, 230)))
        # Borde cian neón
        painter.setPen(QPen(QColor(6, 182, 212, 200), 1.5))
        painter.drawPath(path)
