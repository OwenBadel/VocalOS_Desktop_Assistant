"""
Servidor Principal FastAPI & WebSocket de VocalOS Desktop Assistant.
Expone endpoints REST y canal bidireccional WebSocket para telemetría,
verificación biométrica vocal, ejecución de comandos en terminal y control del SO.
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .biometrics_service import VoiceBiometricsService
from .os_controller import OSController
from .fs_manager import FileSystemManager
from .browser_controller import BrowserController
from .entertainment_manager import EntertainmentManager
from .intent_parser import IntentParser

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="VocalOS Desktop Assistant API",
    description="Backend operativo de escritorio con biometría vocal y control autónomo de Windows.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicios
bio_service = VoiceBiometricsService(data_dir=BASE_DIR / "data")
os_ctrl = OSController()
fs_mgr = FileSystemManager(workspace_root=BASE_DIR)
browser_ctrl = BrowserController()
ent_mgr = EntertainmentManager()
intent_parser = IntentParser(os_ctrl, fs_mgr, browser_ctrl, ent_mgr)


# Schemas Pydantic
class EnrollRequest(BaseModel):
    user_name: str
    samples: List[List[float]]  # Lista de arrays de características acústicas
    threshold: float = 0.78


class ProcessVoiceRequest(BaseModel):
    transcript: str
    audio_features: Optional[List[float]] = None
    bypass_biometrics: bool = False


class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None


class FileCreateRequest(BaseModel):
    path: str
    content: str = ""


class FileEditRequest(BaseModel):
    path: str
    content: str
    append: bool = False


class FileDeleteRequest(BaseModel):
    path: str


class SearchRequest(BaseModel):
    query: str
    engine: Optional[str] = "google"


class GameRequest(BaseModel):
    game_name: str


class SpotifyRequest(BaseModel):
    query: Optional[str] = None


class FolderRequest(BaseModel):
    folder: str


# Endpoints API REST
@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "assistant_name": "VocalOS",
        "autonomy_enabled": os_ctrl.autonomy_enabled,
        "biometrics": bio_service.get_status()
    }


@app.post("/api/profile/enroll")
def enroll_profile(req: EnrollRequest):
    try:
        sample_vectors = [np.array(s, dtype=np.float32) for s in req.samples]
        profile = bio_service.enroll_profile(
            user_name=req.user_name,
            sample_vectors=sample_vectors,
            threshold=req.threshold
        )
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/profile/status")
def get_profile_status():
    return bio_service.get_status()


@app.post("/api/voice/process")
def process_voice_command(req: ProcessVoiceRequest):
    """
    Procesa un comando vocal transcrito. Si se envían características acústicas,
    primero verifica la huella biométrica del usuario.
    """
    is_verified = True
    confidence = 1.0
    biometric_msg = "Verificación omitida por configuración."

    if not req.bypass_biometrics and bio_service.profile:
        if req.audio_features:
            test_vec = np.array(req.audio_features, dtype=np.float32)
            # Similitud directa contra la huella
            target_vec = np.array(bio_service.profile["voiceprint"], dtype=np.float32)
            from scipy.spatial.distance import cosine
            dist = cosine(target_vec, test_vec)
            confidence = float(max(0.0, 1.0 - dist))
            threshold = bio_service.profile.get("threshold", 0.78)
            is_verified = confidence >= threshold
            
            if is_verified:
                biometric_msg = f"Voz autorizada de {bio_service.profile.get('user_name')} ({confidence*100:.1f}%)"
            else:
                biometric_msg = f"Acceso denegado: Huella acústica no coincide ({confidence*100:.1f}% < {threshold*100:.1f}%)"
        else:
            # Si hay perfil pero no audio, no autoriza si la seguridad es estricta
            is_verified = False
            biometric_msg = "Muestra de audio no proporcionada para verificación de locutor."

    if not is_verified:
        return {
            "authorized": False,
            "biometric_confidence": confidence,
            "message": biometric_msg,
            "execution": None
        }

    # Si la biometría fue aprobada, procesar el comando
    result = intent_parser.parse_and_execute(req.transcript)
    return {
        "authorized": True,
        "biometric_confidence": confidence,
        "message": biometric_msg,
        "execution": result
    }


@app.post("/api/terminal/execute")
def execute_terminal(req: CommandRequest):
    res = os_ctrl.run_command_sync(req.command, cwd=req.cwd)
    return res


@app.post("/api/files/create")
def create_file(req: FileCreateRequest):
    return fs_mgr.create_file(req.path, req.content)


@app.get("/api/files/read")
def read_file(path: str):
    return fs_mgr.read_file(path)


@app.post("/api/files/edit")
def edit_file(req: FileEditRequest):
    return fs_mgr.edit_file(req.path, req.content, req.append)


@app.post("/api/files/delete")
def delete_file(req: FileDeleteRequest):
    return fs_mgr.delete_file(req.path)


@app.get("/api/files/list")
def list_files(dirpath: str = "."):
    return fs_mgr.list_dir(dirpath)


@app.post("/api/folder/open")
def open_folder(req: FolderRequest):
    return os_ctrl.open_folder(req.folder)


@app.post("/api/entertainment/game")
def launch_game(req: GameRequest):
    return ent_mgr.launch_game(req.game_name)


@app.post("/api/entertainment/spotify")
def open_spotify(req: SpotifyRequest):
    return ent_mgr.open_spotify(req.query)


@app.post("/api/entertainment/anime")
def search_anime(title: str, portal: str = "animeflv"):
    return ent_mgr.search_anime_movie(title, portal=portal)


@app.post("/api/browser/search")
def search_browser(req: SearchRequest):
    return browser_ctrl.search(req.query, engine=req.engine)


# WebSocket para streaming de terminal y telemetría
@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({"type": "info", "message": "Conexión a Terminal VocalOS establecida."})
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "run":
                command = payload.get("command", "")
                cwd = payload.get("cwd")
                async for event in os_ctrl.run_command_stream(command, cwd=cwd):
                    await websocket.send_json(event)
            elif action == "ping":
                await websocket.send_json({"type": "pong", "time": str(np.datetime64("now"))})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# Montar interfaz frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
