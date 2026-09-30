"""
Gestor de Entretenimiento, Videojuegos y Multimedia.
Controla el lanzamiento de videojuegos (R.E.P.O., PEAK, clientes de Steam),
la reproducción y búsqueda de música en Spotify y la apertura de anime y películas.
"""

from __future__ import annotations
import os
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional


class EntertainmentManager:
    # IDs o URIs para títulos solicitados
    KNOWN_GAMES = {
        "repo": {
            "title": "R.E.P.O.",
            "steam_uri": "steam://rungameid/3241660",  # ID Steam o fallback de búsqueda
            "fallback_query": "R.E.P.O. game steam",
            "aliases": ["repo", "r.e.p.o.", "r.e.p.o", "el repo"]
        },
        "peak": {
            "title": "PEAK",
            "steam_uri": "steam://rungameid/peak",
            "fallback_query": "PEAK videogame",
            "aliases": ["peak", "el peak", "juego peak"]
        },
        "steam": {
            "title": "Steam Client",
            "steam_uri": "steam://open/main",
            "fallback_query": "steam client",
            "aliases": ["steam", "tienda steam"]
        }
    }

    def __init__(self, media_folder: Optional[Path] = None):
        self.media_folder = media_folder or Path.home() / "Videos"

    def launch_game(self, game_name: str) -> Dict:
        """
        Inicia un videojuego a través del protocolo nativo de Steam o acceso directo.
        """
        clean_name = game_name.strip().lower()
        matched_game = None

        for key, info in self.KNOWN_GAMES.items():
            if clean_name in info["aliases"] or key in clean_name:
                matched_game = info
                break

        if matched_game:
            uri = matched_game["steam_uri"]
            title = matched_game["title"]
            try:
                # En Windows, 'start <uri>' o 'explorer <uri>' invoca el handler de Steam
                os.system(f'start "" "{uri}"')
                return {
                    "success": True,
                    "game": title,
                    "launch_uri": uri,
                    "message": f"Iniciando {title} a través de Steam..."
                }
            except Exception as e:
                return {"success": False, "game": title, "error": str(e)}

        # Si no es un juego mapeado directamente, intentar buscar en Steam o abrir navegador
        encoded = urllib.parse.quote_plus(game_name)
        search_uri = f"steam://store/search/?term={encoded}"
        try:
            os.system(f'start "" "{search_uri}"')
            return {
                "success": True,
                "game": game_name,
                "launch_uri": search_uri,
                "message": f"Buscando '{game_name}' en la biblioteca y tienda de Steam..."
            }
        except Exception:
            webbrowser.open(f"https://store.steampowered.com/search/?term={encoded}")
            return {
                "success": True,
                "game": game_name,
                "message": f"Abriendo tienda web para: '{game_name}'"
            }

    def open_spotify(self, query: Optional[str] = None) -> Dict:
        """
        Abre la aplicación nativa de Spotify o ejecuta una búsqueda de música/podcast.
        """
        try:
            if query:
                encoded = urllib.parse.quote(query.strip())
                uri = f"spotify:search:{encoded}"
                os.system(f'start "" "{uri}"')
                msg = f"Buscando en Spotify: '{query}'"
            else:
                os.system('start "" "spotify:"')
                msg = "Spotify abierto correctamente."

            return {
                "success": True,
                "service": "Spotify",
                "query": query,
                "message": msg
            }
        except Exception as e:
            return {"success": False, "service": "Spotify", "error": str(e)}

    def search_anime_movie(self, title: str, portal: str = "animeflv") -> Dict:
        """
        Busca y abre un anime o película en el portal seleccionado o en el navegador.
        """
        portals = {
            "animeflv": "https://www3.animeflv.net/browse?q={q}",
            "crunchyroll": "https://www.crunchyroll.com/search?q={q}",
            "netflix": "https://www.netflix.com/search?q={q}",
            "cuevana": "https://cuevana.biz/buscar?q={q}",
            "youtube": "https://www.youtube.com/results?search_query={q}+anime"
        }
        
        target_template = portals.get(portal.lower(), portals["animeflv"])
        encoded = urllib.parse.quote_plus(title.strip())
        url = target_template.format(q=encoded)
        
        try:
            webbrowser.open(url, new=2)
            return {
                "success": True,
                "title": title,
                "portal": portal,
                "url": url,
                "message": f"Abriendo portal de anime ({portal.capitalize()}) para: '{title}'"
            }
        except Exception as e:
            return {"success": False, "title": title, "error": str(e)}

    def open_media_folder(self, category: str = "anime") -> Dict:
        """Abre la carpeta local de descargas de anime o películas."""
        home = Path.home()
        target = home / "Videos" / category.capitalize()
        target.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(["explorer.exe", str(target)])
            return {
                "success": True,
                "category": category,
                "path": str(target),
                "message": f"Carpeta local de {category} abierta en el explorador."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
