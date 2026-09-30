"""
Controlador Autónomo del Sistema Operativo Windows.
Ejecuta comandos de PowerShell / CMD en procesos asíncronos desacoplados,
gestiona captura de salida y permite abrir carpetas nativas con Windows Explorer.
"""

from __future__ import annotations
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional


class OSController:
    def __init__(self, default_cwd: Optional[Path] = None):
        self.default_cwd = default_cwd or Path.home()
        self.history: List[Dict] = []
        self.autonomy_enabled = True

    def set_autonomy(self, enabled: bool):
        """Activa o suspende la autorización de ejecución autónoma."""
        self.autonomy_enabled = enabled

    def run_command_sync(self, command: str, cwd: Optional[str] = None, timeout: int = 30) -> Dict:
        """
        Ejecuta un comando en PowerShell de forma síncrona con control de timeout.
        """
        if not self.autonomy_enabled:
            return {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Autorización autónoma deshabilitada por el usuario.",
                "success": False
            }

        work_dir = cwd if cwd and os.path.isdir(cwd) else str(self.default_cwd)
        try:
            # Ejecutar con PowerShell en Windows o Shell estándar
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            data = {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "success": result.returncode == 0
            }
            self.history.append(data)
            return data
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "exit_code": -2,
                "stdout": "",
                "stderr": f"Tiempo de espera expirado tras {timeout} segundos.",
                "success": False
            }
        except Exception as e:
            return {
                "command": command,
                "exit_code": -3,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }

    async def run_command_stream(self, command: str, cwd: Optional[str] = None) -> AsyncGenerator[Dict, None]:
        """
        Ejecuta un comando en PowerShell transmitiendo stdout y stderr línea a línea en tiempo real.
        Ideal para streaming a través de WebSockets hacia la consola de la UI.
        """
        if not self.autonomy_enabled:
            yield {"type": "error", "line": "Autorización de terminal suspendida temporalmente."}
            return

        work_dir = cwd if cwd and os.path.isdir(cwd) else str(self.default_cwd)
        yield {"type": "meta", "line": f"[VocalOS] Ejecutando: {command} en {work_dir}"}

        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-Command", command,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            async def read_stream(stream, stream_type):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("cp1252", errors="replace").rstrip()
                    yield {"type": stream_type, "line": decoded}

            async for item in read_stream(process.stdout, "stdout"):
                yield item

            async for item in read_stream(process.stderr, "stderr"):
                yield item

            exit_code = await process.wait()
            yield {"type": "exit", "exit_code": exit_code, "line": f"[VocalOS] Proceso terminado con código {exit_code}"}
        except Exception as e:
            yield {"type": "error", "line": f"[VocalOS Error] {str(e)}"}

    def open_folder(self, folder_query: str) -> Dict:
        """
        Abre una carpeta del sistema operativo en el Explorador de Windows (explorer.exe).
        Resuelve nombres amigables (ej: 'descargas', 'documentos', 'escritorio', 'proyectos').
        """
        home = Path.home()
        query_lower = folder_query.strip().lower()

        # Mapeo de atajos comunes en español
        shortcuts = {
            "descargas": home / "Downloads",
            "downloads": home / "Downloads",
            "documentos": home / "Documents",
            "documents": home / "Documents",
            "escritorio": home / "Desktop",
            "desktop": home / "Desktop",
            "musica": home / "Music",
            "music": home / "Music",
            "imagenes": home / "Pictures",
            "fotos": home / "Pictures",
            "videos": home / "Videos",
            "proyectos": Path("d:/Proyectos"),
            "fabrica": Path("d:/Proyectos/LemonFabrica/Fabrica_Software"),
            "anime": home / "Videos" / "Anime"
        }

        target_path: Optional[Path] = None
        for key, path in shortcuts.items():
            if key in query_lower:
                target_path = path
                break

        if not target_path:
            # Si no es atajo conocido, verificar si es ruta absoluta o relativa válida
            candidate = Path(folder_query)
            if candidate.exists() and candidate.is_dir():
                target_path = candidate
            else:
                # Buscar subcarpeta en home
                sub = home / folder_query
                if sub.exists() and sub.is_dir():
                    target_path = sub
                else:
                    target_path = home

        # Iniciar explorer.exe de Windows
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["explorer.exe", str(target_path.resolve())])
            return {
                "success": True,
                "path": str(target_path.resolve()),
                "message": f"Carpeta abierta en explorador: {target_path.name}"
            }
        except Exception as e:
            return {
                "success": False,
                "path": str(target_path),
                "error": str(e)
            }
