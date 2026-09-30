"""
Gestor de Sistema de Archivos (FileSystem Manager).
Permite crear, leer, editar y eliminar archivos y carpetas por peticiones del usuario.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union


class FileSystemManager:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.home()

    def resolve_path(self, filepath: str) -> Path:
        """Resuelve rutas relativas contra el workspace o absolutas directas."""
        path = Path(filepath)
        if not path.is_absolute():
            path = (self.workspace_root / path).resolve()
        return path

    def create_file(self, filepath: str, content: str = "") -> Dict:
        """Crea un archivo nuevo con el contenido indicado."""
        try:
            target = self.resolve_path(filepath)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "action": "create",
                "path": str(target),
                "bytes_written": len(content.encode("utf-8")),
                "message": f"Archivo creado exitosamente: {target.name}"
            }
        except Exception as e:
            return {"success": False, "action": "create", "error": str(e)}

    def read_file(self, filepath: str, max_lines: int = 200) -> Dict:
        """Lee el contenido de un archivo de texto."""
        try:
            target = self.resolve_path(filepath)
            if not target.exists():
                return {"success": False, "error": f"El archivo '{filepath}' no existe."}
            
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)
            
            return {
                "success": True,
                "action": "read",
                "path": str(target),
                "content": content,
                "total_lines_read": len(lines)
            }
        except Exception as e:
            return {"success": False, "action": "read", "error": str(e)}

    def edit_file(self, filepath: str, content: str, append: bool = False) -> Dict:
        """Edita un archivo existente (sobrescribe o añade contenido)."""
        try:
            target = self.resolve_path(filepath)
            if not target.exists() and not append:
                return {"success": False, "error": f"El archivo '{filepath}' no existe para edición."}
            
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(target, mode, encoding="utf-8") as f:
                f.write(content)
                
            return {
                "success": True,
                "action": "edit",
                "mode": "append" if append else "overwrite",
                "path": str(target),
                "message": f"Archivo modificado correctamente: {target.name}"
            }
        except Exception as e:
            return {"success": False, "action": "edit", "error": str(e)}

    def delete_file(self, filepath: str) -> Dict:
        """Elimina un archivo o directorio de forma segura."""
        try:
            target = self.resolve_path(filepath)
            if not target.exists():
                return {"success": False, "error": f"El archivo '{filepath}' no existe."}
            
            if target.is_dir():
                shutil.rmtree(target)
                msg = f"Directorio eliminado: {target.name}"
            else:
                target.unlink()
                msg = f"Archivo eliminado: {target.name}"

            return {
                "success": True,
                "action": "delete",
                "path": str(target),
                "message": msg
            }
        except Exception as e:
            return {"success": False, "action": "delete", "error": str(e)}

    def list_dir(self, dirpath: str = ".") -> Dict:
        """Lista el contenido de un directorio con metadatos."""
        try:
            target = self.resolve_path(dirpath)
            if not target.exists() or not target.is_dir():
                return {"success": False, "error": f"La ruta '{dirpath}' no es un directorio válido."}
            
            entries = []
            for item in target.iterdir():
                entries.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else None
                })
                
            return {
                "success": True,
                "action": "list",
                "path": str(target),
                "entries": entries[:100]
            }
        except Exception as e:
            return {"success": False, "action": "list", "error": str(e)}
