"""
Parser de Intenciones y Comandos Semánticos de Voz.
Analiza las peticiones de voz transcritas y las clasifica en intenciones de acción:
terminal, navegador, archivos, carpetas, videojuegos (R.E.P.O., PEAK), anime y spotify.
"""

from __future__ import annotations
import re
from typing import Any, Dict, Optional
from .os_controller import OSController
from .fs_manager import FileSystemManager
from .browser_controller import BrowserController
from .entertainment_manager import EntertainmentManager


class IntentParser:
    def __init__(
        self,
        os_ctrl: OSController,
        fs_mgr: FileSystemManager,
        browser_ctrl: BrowserController,
        ent_mgr: EntertainmentManager
    ):
        self.os_ctrl = os_ctrl
        self.fs_mgr = fs_mgr
        self.browser_ctrl = browser_ctrl
        self.ent_mgr = ent_mgr

    def parse_and_execute(self, transcript: str) -> Dict[str, Any]:
        """
        Analiza la frase transcrita por voz y ejecuta la acción correspondiente.
        """
        text = transcript.strip().lower()
        if not text:
            return {"intent": "empty", "success": False, "message": "Petición de voz vacía."}

        # 1. Intención: Abrir Carpetas por Voz
        # Ejemplos: "abre la carpeta descargas", "abrir carpeta de proyectos", "abre mis documentos"
        folder_match = re.search(r"(?:abre|abrir|mostrar|ver)\s+(?:la\s+)?carpeta\s+(?:de\s+)?([a-záéíóú0-9_\-\\/\.\s]+)", text)
        if folder_match:
            folder_name = folder_match.group(1).strip()
            res = self.os_ctrl.open_folder(folder_name)
            return {"intent": "open_folder", "target": folder_name, "result": res}

        # 2. Intención: Videojuegos (R.E.P.O., PEAK, etc.)
        # Ejemplos: "inicia repo", "abre r.e.p.o.", "jugar peak", "abre el juego peak", "inicia steam"
        game_match = re.search(r"(?:inicia|iniciar|abre|abrir|jugar|pon|ejecuta)\s+(?:el\s+juego\s+|el\s+)?(repo|r\.e\.p\.o\.|peak|steam)", text)
        if game_match:
            game_name = game_match.group(1).strip()
            res = self.ent_mgr.launch_game(game_name)
            return {"intent": "launch_game", "game": game_name, "result": res}

        # 3. Intención: Música / Spotify
        # Ejemplos: "abre spotify", "pon musica en spotify", "busca queen en spotify"
        if "spotify" in text:
            search_query = None
            spot_match = re.search(r"(?:busca|reproduce|pon)\s+(.+?)\s+en\s+spotify", text)
            if spot_match:
                search_query = spot_match.group(1).strip()
            res = self.ent_mgr.open_spotify(search_query)
            return {"intent": "spotify", "query": search_query, "result": res}

        # 4. Intención: Anime y Películas
        # Ejemplos: "busca anime solo leveling", "ver anime frieren", "abre la pelicula interstellar"
        anime_match = re.search(r"(?:busca|ver|abre|pon)\s+(?:el\s+)?anime\s+(.+)", text)
        if anime_match:
            title = anime_match.group(1).strip()
            res = self.ent_mgr.search_anime_movie(title, portal="animeflv")
            return {"intent": "anime", "title": title, "result": res}

        movie_match = re.search(r"(?:busca|ver|abre|pon)\s+(?:la\s+)?pelicula\s+(.+)", text)
        if movie_match:
            title = movie_match.group(1).strip()
            res = self.ent_mgr.search_anime_movie(title, portal="cuevana")
            return {"intent": "movie", "title": title, "result": res}

        # 5. Intención: Operaciones con Archivos (Crear, Editar, Borrar)
        # Crear: "crea el archivo notas.txt con el texto hola mundo"
        create_match = re.search(r"(?:crea|crear|genera|generar)\s+(?:un\s+|el\s+)?archivo\s+([^\s]+)(?:\s+(?:con|de|llamado)\s+(.+))?", text)
        if create_match:
            filename = create_match.group(1).strip()
            content = create_match.group(2).strip() if create_match.group(2) else ""
            res = self.fs_mgr.create_file(filename, content)
            return {"intent": "create_file", "filename": filename, "result": res}

        # Editar: "edita el archivo notas.txt y añade nueva linea"
        edit_match = re.search(r"(?:edita|editar|modifica|modificar)\s+(?:el\s+)?archivo\s+([^\s]+)\s+(?:con|añade|agrega)\s+(.+)", text)
        if edit_match:
            filename = edit_match.group(1).strip()
            content = edit_match.group(2).strip()
            res = self.fs_mgr.edit_file(filename, "\n" + content, append=True)
            return {"intent": "edit_file", "filename": filename, "result": res}

        # Borrar: "borra el archivo notas.txt" o "elimina el archivo temp.log"
        delete_match = re.search(r"(?:borra|borrar|elimina|eliminar)\s+(?:el\s+)?archivo\s+([^\s]+)", text)
        if delete_match:
            filename = delete_match.group(1).strip()
            res = self.fs_mgr.delete_file(filename)
            return {"intent": "delete_file", "filename": filename, "result": res}

        # 6. Intención: Ejecutar en Terminal
        # Ejemplos: "ejecuta en terminal ipconfig", "terminal dir", "corre el comando get-process"
        term_match = re.search(r"(?:ejecuta|ejecutar|corre|correr|terminal)\s+(?:en\s+(?:la\s+)?terminal\s+)?(?:el\s+comando\s+)?(.+)", text)
        if term_match and ("terminal" in text or "comando" in text or text.startswith(("dir", "ipconfig", "ping", "ls"))):
            cmd = term_match.group(1).strip()
            res = self.os_ctrl.run_command_sync(cmd)
            return {"intent": "terminal", "command": cmd, "result": res}

        # 7. Intención: Búsqueda Web General con Navegador Predeterminado
        # Ejemplos: "busca en internet mejores procesadores 2026", "busca como aprender rust", "busca en google ..."
        search_match = re.search(r"(?:busca|buscar|encuentra|investiga)\s+(?:en\s+(?:google|internet|la\s+web)\s+)?(.+)", text)
        if search_match:
            query = search_match.group(1).strip()
            res = self.browser_ctrl.search(query)
            return {"intent": "web_search", "query": query, "result": res}

        # 8. Intención de Fallback: Abrir aplicación o buscar directamente
        res = self.browser_ctrl.search(text)
        return {"intent": "general_search", "query": text, "result": res}
