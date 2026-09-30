"""
Bandeja del Sistema (System Tray) para Ari en Español.
Proporciona control discreto desde la barra de tareas de Windows con PyQt6.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class AriTrayIcon(QSystemTrayIcon):
    """
    Icono en la bandeja del sistema para Ari, con menú contextual en español
    y señales para interactuar con la ventana del personaje y el oyente de voz.
    """
    toggle_visibility_signal = pyqtSignal()
    request_listen_signal = pyqtSignal()
    trigger_command_signal = pyqtSignal(str)
    toggle_pose_signal = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None, icon_path: Optional[Path] = None):
        super().__init__(parent)
        self.icon_path = icon_path or Path(__file__).resolve().parent.parent / "assets" / "character" / "idle1.png"
        self._setup_icon()
        self._setup_menu()
        self.activated.connect(self._on_tray_activated)

    def _setup_icon(self):
        if self.icon_path.exists():
            pixmap = QPixmap(str(self.icon_path))
            scaled = pixmap.scaled(32, 32)
            self.setIcon(QIcon(scaled))
        else:
            # Fallback icono cian dibujado
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            painter.setBrush(QColor(6, 182, 212))
            painter.setPen(QColor(34, 211, 238))
            painter.drawEllipse(4, 4, 24, 24)
            painter.end()
            self.setIcon(QIcon(pixmap))

        self.setToolTip("Ari — Asistente de Escritorio en Español (Owen Badel Hooker)")

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 245);
                color: #f8fafc;
                border: 1px solid #06b6d4;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(6, 182, 212, 0.25);
                color: #22d3ee;
            }
        """)

        # Estado del Asistente (Informativo)
        title_act = QAction("🌸 Ari: Activa (Voz de Owen)", self)
        title_act.setEnabled(False)
        menu.addAction(title_act)
        menu.addSeparator()

        # Acciones operativas
        act_listen = QAction("🎙️ Escuchar orden ahora", self)
        act_listen.triggered.connect(lambda: self.request_listen_signal.emit())
        menu.addAction(act_listen)

        act_vis = QAction("👁️ Mostrar / Ocultar a Ari", self)
        act_vis.triggered.connect(lambda: self.toggle_visibility_signal.emit())
        menu.addAction(act_vis)

        act_pose = QAction("🧘 Cambiar pose (Sentada / De pie)", self)
        act_pose.triggered.connect(lambda: self.toggle_pose_signal.emit())
        menu.addAction(act_pose)

        menu.addSeparator()

        act_vlc = QAction("🎬 Reproducir Owari no Seraph (VLC)", self)
        act_vlc.triggered.connect(lambda: self.trigger_command_signal.emit("reproduceme en vlc el anime owari no seraph"))
        menu.addAction(act_vlc)

        act_anime = QAction("📁 Abrir Carpeta de Anime", self)
        act_anime.triggered.connect(lambda: self.trigger_command_signal.emit("abre la carpeta anime"))
        menu.addAction(act_anime)

        act_repo = QAction("🎮 Iniciar R.E.P.O. (Steam)", self)
        act_repo.triggered.connect(lambda: self.trigger_command_signal.emit("iniciar juego repo"))
        menu.addAction(act_repo)

        menu.addSeparator()

        act_exit = QAction("❌ Salir de Ari", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_exit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        # Al hacer doble clic en el icono del tray, alternar visibilidad del personaje
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility_signal.emit()
