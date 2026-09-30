"""
Despachador Central de Comandos de Voz para el Daemon de Segundo Plano.
Enruta órdenes habladas hacia el buscador de VLC, controlador de SO,
ejecutor de juegos (R.E.P.O./PEAK), Spotify, carpetas y archivos.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .media_searcher import MediaSearcher


class CommandDispatcher:
    def __init__(self, media_searcher: Optional[MediaSearcher] = None):
        self.media_searcher = media_searcher or MediaSearcher()

    def dispatch(self, transcript: str) -> Dict[str, Any]:
        """
        Analiza el texto transcrito de la voz del usuario y ejecuta la acción en segundo plano.
        """
        text = transcript.strip().lower()
        if not text:
            return {"action": "none", "success": False, "message": "Texto vacío."}

        print(f"\n[Dispatcher] Petición recibida: '{transcript}'")

        # 1. Reproducir Anime o Película en VLC (Caso principal solicitado)
        # Ejemplos: "reprodúceme en vlc el anime owari no seraph", "pon owari no seraph en vlc", "ver anime ..."
        vlc_match = re.search(r"(?:reproduce|reprodceme|reproduceme|pon|ver|abre)\s+(?:en\s+vlc\s+)?(?:el\s+)?(?:anime|pelicula|serie)?\s*(.+?)(?:\s+en\s+vlc)?$", text)
        if ("vlc" in text or "anime" in text or "pelicula" in text or "reproduce" in text or "reproduceme" in text or "owari" in text) and not ("spotify" in text or "terminal" in text or "carpeta" in text):
            # Extraer el nombre de la serie
            anime_query = text
            for prefix in ["reprodúceme en vlc el anime", "reproduceme en vlc el anime", "reproduce en vlc el anime",
                           "reprodúceme en vlc", "reproduceme en vlc", "reproduce en vlc", "pon el anime",
                           "abre el anime", "ver el anime", "pon", "abre"]:
                if anime_query.startswith(prefix):
                    anime_query = anime_query[len(prefix):].strip()
                    break

            anime_query = anime_query.replace("en vlc", "").replace("el anime", "").strip()
            if not anime_query:
                anime_query = "Owari no Seraph"

            res = self.media_searcher.search_and_play(anime_query)
            return {"action": "play_vlc", "target": anime_query, "result": res}

        # 2. Abrir Carpetas en Windows Explorer
        folder_match = re.search(r"(?:abre|abrir|mostrar|ver)\s+(?:la\s+)?carpeta\s+(?:de\s+)?([a-záéíóú0-9_\-\\/\.\s]+)", text)
        if folder_match or "carpeta" in text:
            folder_name = folder_match.group(1).strip() if folder_match else text.replace("abre", "").replace("carpeta", "").strip()
            res = self._open_folder(folder_name)
            return {"action": "open_folder", "folder": folder_name, "result": res}

        # 3. Videojuegos (R.E.P.O., PEAK, Steam)
        if any(g in text for g in ["repo", "r.e.p.o.", "peak", "steam"]):
            if "repo" in text:
                os.system('start "" "steam://rungameid/3241660"')
                return {"action": "launch_game", "game": "R.E.P.O.", "success": True, "message": "Iniciando R.E.P.O. en Steam..."}
            elif "peak" in text:
                os.system('start "" "steam://rungameid/peak"')
                return {"action": "launch_game", "game": "PEAK", "success": True, "message": "Iniciando PEAK en Steam..."}
            elif "steam" in text:
                os.system('start "" "steam://open/main"')
                return {"action": "launch_game", "game": "Steam", "success": True, "message": "Abriendo biblioteca de Steam..."}

        # 4. Música en Spotify
        if "spotify" in text:
            spot_match = re.search(r"(?:busca|reproduce|pon)\s+(.+?)\s+en\s+spotify", text)
            if spot_match:
                q = spot_match.group(1).strip()
                import urllib.parse
                os.system(f'start "" "spotify:search:{urllib.parse.quote(q)}"')
                msg = f"Buscando '{q}' en Spotify..."
            else:
                os.system('start "" "spotify:"')
                msg = "Spotify iniciado."
            return {"action": "spotify", "success": True, "message": msg}

        # 5. Comandos de Terminal
        if "terminal" in text or "comando" in text:
            cmd = text.replace("terminal", "").replace("ejecuta en la terminal", "").replace("ejecuta en terminal", "").replace("corre el comando", "").strip()
            try:
                res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=20)
                return {
                    "action": "terminal",
                    "command": cmd,
                    "exit_code": res.returncode,
                    "stdout": res.stdout.strip(),
                    "stderr": res.stderr.strip()
                }
            except Exception as e:
                return {"action": "terminal", "command": cmd, "error": str(e)}

        # 6. Operaciones de Archivos
        if "crea el archivo" in text or "crear archivo" in text:
            match = re.search(r"(?:crea|crear)\s+(?:el\s+)?archivo\s+([^\s]+)(?:\s+con\s+(.+))?", text)
            if match:
                filename = match.group(1)
                content = match.group(2) or ""
                p = Path(filename)
                p.write_text(content, encoding="utf-8")
                return {"action": "create_file", "file": str(p.resolve()), "success": True}

        if "borra el archivo" in text or "elimina el archivo" in text:
            match = re.search(r"(?:borra|elimina)\s+(?:el\s+)?archivo\s+([^\s]+)", text)
            if match:
                filename = match.group(1)
                p = Path(filename)
                if p.exists():
                    p.unlink()
                    return {"action": "delete_file", "file": str(p.resolve()), "success": True}
                return {"action": "delete_file", "file": filename, "success": False, "error": "No existe"}

        # Fallback: Búsqueda multimedia si nada más coincidió
        res = self.media_searcher.search_and_play(text)
        return {"action": "fallback_media", "query": text, "result": res}

    def _open_folder(self, folder_query: str) -> Dict:
        home = Path.home()
        q = folder_query.lower()
        mapping = {
            "descargas": home / "Downloads",
            "documentos": home / "Documents",
            "escritorio": home / "Desktop",
            "musica": home / "Music",
            "videos": home / "Videos",
            "anime": Path("D:/Anime"),
            "proyectos": Path("D:/Proyectos"),
            "d": Path("D:/"),
            "disco d": Path("D:/")
        }

        target = None
        for k, v in mapping.items():
            if k in q:
                target = v
                break

        if not target:
            target = Path(folder_query)
            if not target.exists():
                target = home

        try:
            subprocess.Popen(["explorer.exe", str(target.resolve())])
            return {"success": True, "path": str(target.resolve()), "message": f"Carpeta abierta: {target.name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
