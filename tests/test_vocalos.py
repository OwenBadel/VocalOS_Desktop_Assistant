"""
Suite de Pruebas Automatizadas para VocalOS Desktop Assistant.
Verifica: Biometría Vocal, Controlador de SO, Gestor de Archivos, e Intent Parser.
Autor: Owen Badel Hooker
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np

from backend.biometrics_service import VoiceBiometricsService
from backend.os_controller import OSController
from backend.fs_manager import FileSystemManager
from backend.browser_controller import BrowserController
from backend.entertainment_manager import EntertainmentManager
from backend.intent_parser import IntentParser


class TestVocalOS(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.bio_service = VoiceBiometricsService(data_dir=self.test_dir / "data")
        self.os_ctrl = OSController(default_cwd=self.test_dir)
        self.fs_mgr = FileSystemManager(workspace_root=self.test_dir)
        self.browser_ctrl = BrowserController()
        self.ent_mgr = EntertainmentManager(media_folder=self.test_dir)
        self.intent_parser = IntentParser(self.os_ctrl, self.fs_mgr, self.browser_ctrl, self.ent_mgr)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_voice_biometrics_feature_extraction(self):
        """Verifica que la extracción de características acústicas retorne un vector unitario de 64 elementos."""
        t = np.linspace(0, 1, 16000)
        audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        features = self.bio_service.extract_features(audio, sample_rate=16000)
        self.assertEqual(len(features), 64)
        norm = np.linalg.norm(features)
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_voice_biometrics_enrollment_and_verification(self):
        """Verifica que el perfil de voz se enrole y discrimine entre voz legítima y voz no autorizada."""
        # Generar 3 muestras de calibración para Owen
        t = np.linspace(0, 1, 16000)
        audio_owen_1 = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        audio_owen_2 = (np.sin(2 * np.pi * 445 * t) * 32767).astype(np.int16)
        audio_owen_3 = (np.sin(2 * np.pi * 438 * t) * 32767).astype(np.int16)

        samples = [
            self.bio_service.extract_features(audio_owen_1),
            self.bio_service.extract_features(audio_owen_2),
            self.bio_service.extract_features(audio_owen_3)
        ]

        profile = self.bio_service.enroll_profile(
            user_name="Owen Badel Hooker",
            sample_vectors=samples,
            threshold=0.85
        )
        self.assertEqual(profile["user_name"], "Owen Badel Hooker")

        # Probar con voz legítima similar (442 Hz)
        audio_legit = (np.sin(2 * np.pi * 442 * t) * 32767).astype(np.int16)
        verified, conf, msg = self.bio_service.verify_audio(audio_legit)
        self.assertTrue(verified, f"Voz legítima debería ser verificada (conf: {conf})")
        self.assertIn("Owen Badel Hooker", msg)

        # Probar con voz no autorizada con frecuencia muy diferente (3500 Hz)
        audio_impostor = (np.sin(2 * np.pi * 3500 * t) * 32767).astype(np.int16)
        verified_imp, conf_imp, msg_imp = self.bio_service.verify_audio(audio_impostor)
        self.assertFalse(verified_imp, f"Voz impostor debería ser rechazada (conf: {conf_imp})")
        self.assertIn("Acceso denegado", msg_imp)

    def test_filesystem_manager_crud(self):
        """Verifica que el gestor de archivos cree, lea, edite y borre archivos correctamente."""
        # 1. Crear
        res_create = self.fs_mgr.create_file("test_doc.txt", "Contenido inicial de prueba")
        self.assertTrue(res_create["success"])
        self.assertTrue((self.test_dir / "test_doc.txt").exists())

        # 2. Leer
        res_read = self.fs_mgr.read_file("test_doc.txt")
        self.assertTrue(res_read["success"])
        self.assertEqual(res_read["content"], "Contenido inicial de prueba")

        # 3. Editar (Append)
        res_edit = self.fs_mgr.edit_file("test_doc.txt", "\nSegunda linea", append=True)
        self.assertTrue(res_edit["success"])
        res_read_after = self.fs_mgr.read_file("test_doc.txt")
        self.assertIn("Segunda linea", res_read_after["content"])

        # 4. Borrar
        res_del = self.fs_mgr.delete_file("test_doc.txt")
        self.assertTrue(res_del["success"])
        self.assertFalse((self.test_dir / "test_doc.txt").exists())

    def test_os_controller_run_command(self):
        """Verifica la ejecución de comandos PowerShell de forma autónoma."""
        res = self.os_ctrl.run_command_sync("Write-Output 'VocalOS Test OK'")
        self.assertTrue(res["success"])
        self.assertIn("VocalOS Test OK", res["stdout"])
        self.assertEqual(res["exit_code"], 0)

    def test_intent_parser_routing(self):
        """Verifica que las peticiones transcritas por voz se rutean a sus respectivas intenciones."""
        # 1. Juego (R.E.P.O.)
        r1 = self.intent_parser.parse_and_execute("inicia el juego repo")
        self.assertEqual(r1["intent"], "launch_game")
        self.assertIn("repo", r1["game"])

        # 2. Juego (PEAK)
        r2 = self.intent_parser.parse_and_execute("abre peak")
        self.assertEqual(r2["intent"], "launch_game")

        # 3. Spotify
        r3 = self.intent_parser.parse_and_execute("pon dua lipa en spotify")
        self.assertEqual(r3["intent"], "spotify")
        self.assertEqual(r3["query"], "dua lipa")

        # 4. Anime
        r4 = self.intent_parser.parse_and_execute("busca anime jujutsu kaisen")
        self.assertEqual(r4["intent"], "anime")
        self.assertIn("jujutsu", r4["title"])

        # 5. Archivos por voz
        r5 = self.intent_parser.parse_and_execute("crea el archivo reporte.md con resumen ejecutivo")
        self.assertEqual(r5["intent"], "create_file")
        self.assertEqual(r5["filename"], "reporte.md")

        # 6. Borrar archivo por voz
        r6 = self.intent_parser.parse_and_execute("borra el archivo reporte.md")
        self.assertEqual(r6["intent"], "delete_file")

    def test_media_searcher_and_dispatcher(self):
        """Verifica que el buscador localice anime en disco D: y el despachador arme la orden de VLC."""
        from core.media_searcher import MediaSearcher
        from core.command_dispatcher import CommandDispatcher

        searcher = MediaSearcher()
        dispatcher = CommandDispatcher(media_searcher=searcher)

        # Probar búsqueda de Owari no Seraph
        found = searcher.find_media("Owari no Seraph")
        self.assertIsNotNone(found, "Debe encontrar la carpeta o archivo de Owari no Seraph en D:")
        self.assertIn("Owari", found["title"])

        # Probar despacho del comando que dio el usuario en el audio
        dispatch_res = dispatcher.dispatch("reproduceme en vlc el anime owari no seraph")
        self.assertEqual(dispatch_res["action"], "play_vlc")
        self.assertIn("owari no seraph", dispatch_res["target"].lower())


if __name__ == "__main__":
    unittest.main()
