"""
Buscador de Medios y Lanzador Nativo de VLC.
Escanea discos duros locales (especialmente D:\\Anime y D:\\) para localizar
animes, películas y series, y ejecutarlos automáticamente en VLC Media Player.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import os
import subprocess
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MediaSearcher:
    VLC_PATHS = [
        Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe"),
        Path(r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"),
    ]

    VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".flv", ".wmv")

    DEFAULT_MEDIA_DIRS = [
        Path("D:/Anime"),
        Path("D:/"),
        Path(os.path.expanduser("~/Videos")),
        Path(os.path.expanduser("~/Downloads")),
    ]

    def __init__(self, custom_dirs: Optional[List[Path]] = None):
        self.search_dirs = [p for p in (custom_dirs or self.DEFAULT_MEDIA_DIRS) if p.exists()]
        self.vlc_exe = self._detect_vlc()

    def _detect_vlc(self) -> Optional[str]:
        """Detecta la ubicación de vlc.exe en el sistema."""
        for candidate in self.VLC_PATHS:
            if candidate.exists():
                return str(candidate.resolve())
        # Intentar buscar en PATH
        import shutil
        found = shutil.which("vlc")
        return found if found else None

    def search_and_play(self, query: str, full_screen: bool = True) -> Dict:
        """
        Busca el anime o película en los discos duros y lo reproduce en VLC.
        """
        if not self.vlc_exe:
            return {
                "success": False,
                "error": "No se encontró el ejecutable de VLC en 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe'."
            }

        target = self.find_media(query)
        if not target:
            return {
                "success": False,
                "query": query,
                "error": f"No se encontró ningún anime o archivo multimedia para '{query}' en los discos duros."
            }

        launch_target = target["target_path"]
        title = target["title"]

        # Lanzar VLC en proceso desacoplado
        cmd = [self.vlc_exe]
        if full_screen:
            cmd.append("--fullscreen")
        cmd.append(str(launch_target))

        try:
            subprocess.Popen(cmd)
            return {
                "success": True,
                "query": query,
                "title": title,
                "target_path": str(launch_target),
                "message": f"Reproduciendo en VLC: '{title}' ({target['match_type']})"
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": f"Error al iniciar VLC: {str(e)}"
            }

    def find_media(self, query: str) -> Optional[Dict]:
        """
        Localiza la mejor carpeta o archivo de video correspondiente a la consulta.
        """
        # Limpiar palabras irrelevantes de la consulta
        stop_words = {"reproduce", "reproduceme", "reproducir", "ver", "pon", "abre", "en", "vlc", "el", "la", "anime", "pelicula", "serie", "de", "del"}
        tokens = [w.lower() for w in query.split() if w.lower() not in stop_words and len(w) > 2]
        
        if not tokens:
            tokens = [w.lower() for w in query.split() if len(w) > 1]

        candidates: List[Tuple[float, Dict]] = []

        for base_dir in self.search_dirs:
            try:
                for root, dirs, files in os.walk(base_dir):
                    dir_name = os.path.basename(root).lower()
                    
                    # 1. Puntuación de carpeta
                    dir_score = sum(3 for t in tokens if t in dir_name)
                    video_files = [os.path.join(root, f) for f in files if f.lower().endswith(self.VIDEO_EXTENSIONS)]

                    if video_files and dir_score > 0:
                        video_files.sort()
                        # Preferir pasar la carpeta para que VLC cargue la lista completa de capítulos
                        candidates.append((
                            dir_score * 2.0,
                            {
                                "title": os.path.basename(root),
                                "target_path": root if len(video_files) > 1 else video_files[0],
                                "match_type": f"Carpeta con {len(video_files)} capítulos" if len(video_files) > 1 else "Archivo único",
                                "first_file": video_files[0]
                            }
                        ))

                    # 2. Puntuación de archivos individuales
                    for f in files:
                        if f.lower().endswith(self.VIDEO_EXTENSIONS):
                            f_lower = f.lower()
                            file_score = sum(2 for t in tokens if t in f_lower)
                            if file_score > 0:
                                candidates.append((
                                    file_score,
                                    {
                                        "title": f,
                                        "target_path": os.path.join(root, f),
                                        "match_type": "Archivo de video",
                                        "first_file": os.path.join(root, f)
                                    }
                                ))

                    # Si escaneamos raíz de D:\, no profundizar innecesariamente en carpetas del sistema
                    if str(base_dir).upper() in ["D:\\", "D:/", "C:\\", "C:/"] and root.count(os.sep) > 3:
                        dirs.clear()

            except Exception:
                continue

        if not candidates:
            return None

        # Ordenar por mayor puntuación
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
