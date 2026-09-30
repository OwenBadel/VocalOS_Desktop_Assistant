"""
Lanzador Principal de VocalOS Desktop Assistant.
Inicia el servidor backend FastAPI/WebSocket y abre la interfaz de escritorio en el navegador predeterminado.
Autor: Owen Badel Hooker
"""

import sys
import webbrowser
import uvicorn
from pathlib import Path

# Asegurar path raíz en sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print("=" * 60)
    print("🎙️  VOCALOS DESKTOP ASSISTANT — SISTEMA OPERATIVO POR VOZ")
    print(f"🚀  Iniciando servidor en {url}")
    print("🛡️  Verificación Biométrica de Locutor: ACTIVA")
    print("=" * 60)

    # Abrir navegador predeterminado automáticamente
    webbrowser.open(url)

    # Iniciar servidor ASGI
    uvicorn.run("backend.server:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
