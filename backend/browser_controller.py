"""
Controlador de Navegador Web y Búsquedas del Sistema.
Utiliza el navegador predeterminado de Windows para realizar consultas en motores
de búsqueda, portales de streaming, YouTube y plataformas especializadas.
"""

from __future__ import annotations
import urllib.parse
import webbrowser
from typing import Dict, Optional


class BrowserController:
    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q={query}",
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "youtube": "https://www.youtube.com/results?search_query={query}",
        "animeflv": "https://www3.animeflv.net/browse?q={query}",
        "crunchyroll": "https://www.crunchyroll.com/search?q={query}",
        "myanimelist": "https://myanimelist.net/search/all?q={query}"
    }

    def __init__(self, default_engine: str = "google"):
        self.default_engine = default_engine

    def search(self, query: str, engine: Optional[str] = None) -> Dict:
        """
        Abre el navegador predeterminado y ejecuta la búsqueda especificada.
        """
        engine_key = (engine or self.default_engine).lower()
        template = self.SEARCH_ENGINES.get(engine_key, self.SEARCH_ENGINES["google"])
        
        encoded_query = urllib.parse.quote_plus(query.strip())
        target_url = template.format(query=encoded_query)

        try:
            opened = webbrowser.open(target_url, new=2)
            return {
                "success": opened,
                "engine": engine_key,
                "query": query,
                "url": target_url,
                "message": f"Búsqueda lanzada en {engine_key.capitalize()}: '{query}'"
            }
        except Exception as e:
            return {
                "success": False,
                "engine": engine_key,
                "query": query,
                "error": str(e)
            }

    def open_url(self, url: str) -> Dict:
        """Abre un URL directo en el navegador predeterminado."""
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        try:
            opened = webbrowser.open(clean_url, new=2)
            return {
                "success": opened,
                "url": clean_url,
                "message": f"URL abierta en navegador: {clean_url}"
            }
        except Exception as e:
            return {"success": False, "url": clean_url, "error": str(e)}
