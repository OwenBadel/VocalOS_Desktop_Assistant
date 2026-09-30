"""
Registro de Comandos en Español para Ari (Ari-VoiceCommand en Español).
Implementa todas las capacidades nativas de Ari: control de VLC, videojuegos (R.E.P.O./PEAK),
Spotify, volumen, capturas de pantalla, carpetas, archivos y terminal.
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import datetime
import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.media_searcher import MediaSearcher


class CommandRegistry:
    def __init__(self, media_searcher: Optional[MediaSearcher] = None):
        self.media_searcher = media_searcher or MediaSearcher()

    def handle_command(self, transcript: str) -> Tuple[bool, str, str]:
        """
        Procesa el texto reconocido en español y ejecuta la acción correspondiente.
        Retorna (exito: bool, respuesta_verbal_tts: str, tipo_accion: str).
        """
        raw = transcript.strip().lower()
        if not raw:
            return False, "No te he escuchado claramente.", "none"

        # Quitar el wake word si está presente al inicio
        text = raw
        for wake in ["ari,", "ari ", "oye ari,", "oye ari ", "aura,", "aura ", "vocalos,", "vocalos "]:
            if text.startswith(wake):
                text = text[len(wake):].strip()
                break

        print(f"\n[Ari CommandRegistry] Ejecutando orden: '{text}' (Original: '{raw}')")

        # 1. VLC & ANIME (Caso prioritario del usuario)
        # "reprodúceme en vlc el anime owari no seraph", "pon el anime owari no seraph", "ver anime ..."
        if any(k in text for k in ["vlc", "anime", "pelicula", "película", "reproduce", "reproduceme", "owari", "serie"]):
            if not any(k in text for k in ["spotify", "terminal", "carpeta"]):
                # Limpiar prefijos de comando con y sin tildes
                clean_query = re.sub(
                    r"^(?:reprod[uú]ceme|reproduce|pon|abre|busca|ver)\s+(?:en\s+vlc\s+)?(?:el\s+anime\s+|la\s+pel[ií]cula\s+|la\s+serie\s+)?",
                    "",
                    text,
                    flags=re.IGNORECASE
                ).strip()
                clean_query = re.sub(r"\b(?:en\s+vlc|el\s+anime|la\s+pel[ií]cula|la\s+serie)\b", "", clean_query, flags=re.IGNORECASE).strip()
                
                anime_query = clean_query if clean_query else "Owari no Seraph"

                res = self.media_searcher.search_and_play(anime_query)
                if res.get("success"):
                    title = res.get("title", anime_query)
                    return True, f"Reproduciendo {title} en VLC.", "play_vlc"
                else:
                    return False, f"No encontré el anime {anime_query} en tus discos.", "play_vlc_error"

        # 2. VIDEOJUEGOS (R.E.P.O., PEAK, STEAM)
        if "repo" in text or "r.e.p.o." in text:
            os.system('start "" "steam://rungameid/3241660"')
            return True, "Iniciando R.E.P.O. en Steam. ¡Que te diviertas!", "game_repo"

        if "peak" in text:
            os.system('start "" "steam://rungameid/peak"')
            return True, "Iniciando PEAK en Steam.", "game_peak"

        if "steam" in text and any(w in text for w in ["abre", "inicia", "abrir", "tienda"]):
            os.system('start "" "steam://open/main"')
            return True, "Abriendo biblioteca de Steam.", "open_steam"

        # 3. MÚSICA EN SPOTIFY
        if "spotify" in text:
            match_song = re.search(r"(?:busca|reproduce|pon)\s+(.+?)\s+en\s+spotify", text)
            if match_song:
                song = match_song.group(1).strip()
                os.system(f'start "" "spotify:search:{urllib.parse.quote(song)}"')
                return True, f"Buscando {song} en Spotify.", "spotify_search"
            else:
                os.system('start "" "spotify:"')
                return True, "Spotify abierto.", "spotify_open"

        # 4. CONTROL DE VOLUMEN DE WINDOWS
        if "sube el volumen" in text or "subir volumen" in text or "más volumen" in text:
            # Enviar 5 pulsaciones de tecla de subir volumen
            subprocess.run(["powershell.exe", "-Command", "1..5 | ForEach-Object { (New-Object -ComObject WScript.Shell).SendKeys([char]175) }"], capture_output=True)
            return True, "Volumen aumentado.", "volume_up"

        if "baja el volumen" in text or "bajar volumen" in text or "menos volumen" in text:
            subprocess.run(["powershell.exe", "-Command", "1..5 | ForEach-Object { (New-Object -ComObject WScript.Shell).SendKeys([char]174) }"], capture_output=True)
            return True, "Volumen reducido.", "volume_down"

        if "silencia" in text or "mute" in text or "quitar volumen" in text:
            subprocess.run(["powershell.exe", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], capture_output=True)
            return True, "Audio silenciado.", "volume_mute"

        # 5. HORA Y FECHA
        if "hora" in text and any(w in text for w in ["qué", "dime", "la", "tienes"]):
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")
            return True, f"Son las {time_str}.", "time"

        if "fecha" in text or "día" in text:
            now = datetime.datetime.now()
            dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            dia = dias[now.weekday()]
            return True, f"Hoy es {dia}, {now.day} de {now.strftime('%B')}.", "date"

        # 6. CAPTURA DE PANTALLA
        if "captura" in text or "screenshot" in text:
            try:
                from PIL import ImageGrab
                screen = ImageGrab.grab()
                save_dir = Path.home() / "Pictures" / "Screenshots"
                save_dir.mkdir(parents=True, exist_ok=True)
                filename = f"Captura_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                full_path = save_dir / filename
                screen.save(str(full_path))
                return True, f"Captura de pantalla guardada en tus Imágenes.", "screenshot"
            except Exception as e:
                return False, f"No pude guardar la captura: {e}", "screenshot_error"

        # 7. APERTURA DE CARPETAS DE WINDOWS
        folder_match = re.search(r"(?:abre|abrir|mostrar|ver)\s+(?:la\s+)?carpeta\s+(?:de\s+)?([a-záéíóú0-9_\-\\/\.\s]+)", text)
        if folder_match or "carpeta" in text:
            target_query = folder_match.group(1).strip() if folder_match else text.replace("abre", "").replace("carpeta", "").strip()
            folder_path = self._resolve_folder(target_query)
            try:
                subprocess.Popen(["explorer.exe", str(folder_path.resolve())])
                return True, f"Abriendo la carpeta {folder_path.name}.", "open_folder"
            except Exception as e:
                return False, f"No pude abrir la carpeta: {e}", "open_folder_error"

        # 8. OPERACIONES DE ARCHIVOS
        if "crea el archivo" in text or "crear archivo" in text:
            match = re.search(r"(?:crea|crear)\s+(?:el\s+)?archivo\s+([^\s]+)(?:\s+con\s+(.+))?", text)
            if match:
                fname = match.group(1)
                content = match.group(2) or ""
                p = Path(fname)
                p.write_text(content, encoding="utf-8")
                return True, f"Archivo {fname} creado con éxito.", "create_file"

        if "borra el archivo" in text or "elimina el archivo" in text:
            match = re.search(r"(?:borra|elimina)\s+(?:el\s+)?archivo\s+([^\s]+)", text)
            if match:
                fname = match.group(1)
                p = Path(fname)
                if p.exists():
                    p.unlink()
                    return True, f"Archivo {fname} eliminado.", "delete_file"
                return False, f"El archivo {fname} no existe.", "delete_file_not_found"

        # 9. TERMINAL POWERSHELL AUTÓNOMA
        if "terminal" in text or "comando" in text:
            cmd = text.replace("terminal", "").replace("ejecuta en la terminal", "").replace("ejecuta en terminal", "").replace("corre el comando", "").strip()
            try:
                res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15)
                output = res.stdout.strip()[:100]
                return True, f"Comando ejecutado con éxito. {output}", "terminal"
            except Exception as e:
                return False, f"Error al ejecutar comando: {e}", "terminal_error"

        # 10. BÚSQUEDA WEB
        if "busca" in text or "buscar" in text:
            query = text.replace("busca en internet", "").replace("busca en google", "").replace("busca", "").strip()
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
            return True, f"Buscando {query} en Google.", "web_search"

        # Fallback de búsqueda de anime/videos
        fallback_res = self.media_searcher.search_and_play(text)
        if fallback_res.get("success"):
            return True, f"Reproduciendo {fallback_res.get('title')} en VLC.", "play_vlc_fallback"

        return False, f"He entendido: '{text}', pero no reconozco esa acción específica.", "unknown"

    def _resolve_folder(self, query: str) -> Path:
        home = Path.home()
        q = query.lower()
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
        for k, v in mapping.items():
            if k in q:
                return v
        candidate = Path(query)
        return candidate if candidate.exists() else home
