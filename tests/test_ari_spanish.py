"""
Suite de Pruebas Automatizadas para Ari en Español (Ari-VoiceCommand ES).
Verifica: MediaSearcher, CommandRegistry (VLC, Steam, anime, carpetas, Spotify, volumen).
Autor: Owen Badel Hooker
"""

from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from core.media_searcher import MediaSearcher
from commands.command_registry import CommandRegistry


class TestAriSpanish(unittest.TestCase):
    def setUp(self):
        self.mock_searcher = MagicMock(spec=MediaSearcher)
        self.registry = CommandRegistry(media_searcher=self.mock_searcher)

    def test_vlc_anime_command_dispatch(self):
        """Verifica que el comando de reproducir anime en VLC invoque al MediaSearcher."""
        self.mock_searcher.search_and_play.return_value = {
            "success": True,
            "title": "Owari no Seraph",
            "file": "D:\\Anime\\Owari No Seraph\\ep01.mkv"
        }
        
        success, tts, action = self.registry.handle_command("reprodúceme en vlc el anime owari no seraph")
        self.assertTrue(success)
        self.assertEqual(action, "play_vlc")
        self.assertIn("Owari no Seraph", tts)
        self.mock_searcher.search_and_play.assert_called_once_with("owari no seraph")

    @patch("os.system")
    def test_steam_repo_game_command(self, mock_os_system):
        """Verifica que el comando de iniciar R.E.P.O. invoque el launcher de Steam."""
        success, tts, action = self.registry.handle_command("ari abre el juego repo")
        self.assertTrue(success)
        self.assertEqual(action, "game_repo")
        self.assertIn("R.E.P.O.", tts)
        mock_os_system.assert_called_once()
        self.assertIn("steam://rungameid/3241660", mock_os_system.call_args[0][0])

    @patch("os.system")
    def test_spotify_command(self, mock_os_system):
        """Verifica que el comando de Spotify busque canciones."""
        success, tts, action = self.registry.handle_command("ari busca bohemian rhapsody en spotify")
        self.assertTrue(success)
        self.assertEqual(action, "spotify_search")
        self.assertIn("bohemian rhapsody", tts.lower())
        mock_os_system.assert_called_once()
        self.assertIn("spotify:search:", mock_os_system.call_args[0][0])

    @patch("subprocess.Popen")
    def test_open_anime_folder_command(self, mock_popen):
        """Verifica que el comando de abrir carpeta de anime abra D:\\Anime."""
        success, tts, action = self.registry.handle_command("abre la carpeta anime")
        self.assertTrue(success)
        self.assertEqual(action, "open_folder")
        self.assertIn("Anime", tts)
        mock_popen.assert_called_once()

    def test_wake_word_stripping(self):
        """Verifica que los prefijos de wake word se eliminen limpiamente."""
        self.mock_searcher.search_and_play.return_value = {"success": True, "title": "Owari"}
        success, _, _ = self.registry.handle_command("Oye Ari, reprodúceme el anime Owari no Seraph")
        self.assertTrue(success)
        self.mock_searcher.search_and_play.assert_called_with("owari no seraph")


if __name__ == "__main__":
    unittest.main()
