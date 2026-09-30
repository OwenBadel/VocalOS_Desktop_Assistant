# 🌸 Ari Desktop Assistant & VocalOS (En Español)

> **Asistente de Escritorio con Personaje Animado Flotante, Biometría Vocal Zero-Trust y Control Autónomo de Windows**  
> **Titular y Autoría:** Owen Badel Hooker — Ingeniero de Sistemas  
> **Basado en la arquitectura:** [Ari-VoiceCommand](https://github.com/DO0OG/Ari-VoiceCommand) (Adaptada al 100% en Español)  
> **Proyecto:** `PROJ-014` | **Empaquetado:** Inno Setup Ready

---

## 📌 Visión General
**Ari** es una asistente de escritorio interactiva con un **personaje animado flotante y transparente** (`CharacterWidget`) que vive sobre las ventanas de Windows, acompañado de un bocadillo de diálogo estilo cómic (`SpeechBubble`), presencia en la bandeja del sistema (`AriTrayIcon`) y escucha continua de voz en segundo plano de bajo consumo.

Diseñado para operar desde la cama o lejos del escritorio sin tocar teclado ni ratón:
* *"Reprodúceme en VLC el anime Owari no Seraph"* $\to$ Localiza automáticamente los capítulos en `D:\Anime` y los reproduce en **VLC Media Player**.
* *"Abre la carpeta de anime"* $\to$ Abre el explorador de Windows directamente en `D:\Anime`.
* *"Abre el juego R.E.P.O."* o *"Inicia PEAK"* $\to$ Lanza los juegos a través de Steam.
* *"Busca [canción] en Spotify"* $\to$ Abre Spotify y busca la canción indicada.
* *"Sube el volumen"* / *"Baja el volumen"* $\to$ Ajusta el volumen del sistema Windows.
* *"Captura de pantalla"* $\to$ Toma captura instantánea y la guarda en Imágenes.
* *"Terminal [comando]"* $\to$ Ejecuta scripts o utilidades de PowerShell.

```mermaid
graph TD
    Mic["🎤 Micrófono en Segundo Plano (sounddevice)"] --> VAD["🔊 Detección de Actividad Vocal (VAD RMS)"]
    VAD --> Bio["🛡️ Filtro Biométrico Zero-Trust (Voz de Owen Badel Hooker)"]
    Bio -->|❌ Impostor| Reject["🚫 Bocadillo: 'Voz no autorizada'"]
    Bio -->|✅ Owen Badel Hooker| STT["⚡ Faster-Whisper Local (CPU int8)"]
    STT --> Dispatcher["🧠 CommandRegistry (Español)"]
    
    Dispatcher --> VLC["🎬 VLC Media Player (Owari no Seraph / D:\\Anime)"]
    Dispatcher --> Games["🎮 Steam: R.E.P.O. / PEAK"]
    Dispatcher --> Explorer["📁 Explorador de Windows (Carpetas)"]
    Dispatcher --> Media["🎵 Spotify / Volumen de Windows"]
    Dispatcher --> Term["💻 Terminal PowerShell Autónoma"]

    Dispatcher --> Bubble["💬 Bocadillo de Diálogo (SpeechBubble)"]
    Dispatcher --> TTS["🔊 Síntesis Neuronal (Edge-TTS es-ES-ElviraNeural)"]
    Dispatcher --> Avatar["🌸 Personaje Flotante Animado (Idle / Sit)"]
```

---

## ✨ Características Principales

### 1. 🔐 Laboratorio de Entrenamiento y Perfil Biométrico Vocal
* **Speaker Verification:** Extracción de espectrogramas FFT, pre-énfasis y bancos espectrales normalizados (64 dimensiones) mediante `scipy.signal` y `scipy.fft`.
* **Calibración Guiada:** Grabación de 3 muestras vocales para generar el centroide acústico (Voiceprint) guardado localmente en `data/voice_profile.json`.
* **Umbral Dinámico:** Control deslizante de sensibilidad biométrica (78% por defecto).
* **Osciloscopio & VU Meter:** Visualizador en vivo de forma de onda y vúmetro de 24 segmentos (Cyan $\to$ Violeta $\to$ Rojo).

### 2. 💻 Control Autónomo de Terminal (PowerShell)
* Ejecución de comandos del sistema con streaming en tiempo real vía WebSockets hacia la consola de la UI.
* Switch de autorización autónoma para pausar o reactivar la ejecución de scripts.

### 3. 🎮 Videojuegos y Entretenimiento
* **Videojuegos Steam:** Invocación directa mediante protocolos nativos `steam://rungameid/...` para **R.E.P.O.**, **PEAK** o apertura de la biblioteca de Steam.
* **Anime & Streaming:** Búsqueda y apertura en Crunchyroll, AnimeFLV o carpetas locales de series.
* **Música (Spotify):** Control de reproducción y búsquedas mediante URI `spotify:search:...`.

### 4. 📁 Sistema de Archivos y Apertura de Carpetas por Voz
* **Apertura de Carpetas:** Detección de intenciones vocales ("abre la carpeta descargas", "abre proyectos", "abre anime") e invocación de `explorer.exe <ruta>`.
* **Operaciones CRUD:** Creación, lectura, edición (append/overwrite) y borrado de archivos por voz o interfaz gráfica.

### 5. 🎨 Interfaz de Usuario Creada con Google Stitch
* Implementación del sistema de diseño **"Obsidian Cyber-Glass OS"** generado a través de Stitch MCP.
* Paleta: Abyss Desktop `#060913`, Cyan Neón `#06b6d4`, Violeta Neón `#a855f7` con glassmorphism (`backdrop-filter: blur(24px)`).
* Tipografía: `Space Grotesk` (Titulares), `Inter` (Cuerpo), `JetBrains Mono` (Terminal y telemetría).

---

## 🛠️ Puesta en Marcha

### 🌸 Modo Asistente de Escritorio con Personaje Flotante (Ari)
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar Ari con personaje animado en pantalla y oyente en segundo plano
python run_ari.py

# (Opcional) Probar únicamente la interfaz gráfica sin capturar micrófono
python run_ari.py --no-voice
```

### 🎙️ Modo Daemon Silencioso (Headless)
```bash
# Ejecutar en segundo plano en consola pura
python vocalos_daemon.py

# O ejecutar con icono en la Bandeja del Sistema (System Tray)
python vocalos_daemon.py --tray
```

### 🧪 Probar el Pipeline Completo con Audio de Prueba
```bash
python simulate_voice_command.py
```

### 📦 Compilación a Ejecutable e Instalador con Inno Setup
1. Compilar los binarios con PyInstaller:
   ```bash
   packaging\build_executable.bat
   ```
2. Compilar el instalador con Inno Setup:
   - Abrir y compilar `packaging\VocalOS_Installer.iss` en **Inno Setup Compiler**.
   - Se generará el instalador final `dist\VocalOS_Instalador_v1.0.exe` con opción de autoinicio con Windows.

---

## 🧪 Pruebas Automatizadas
Para ejecutar la suite de pruebas unitarias:
```bash
python -m unittest tests/test_vocalos.py
```

---

## 🗣️ Ejemplos de Comandos Vocales Soportados

| Intención | Comando Hablado de Ejemplo | Acción Ejecutada |
| :--- | :--- | :--- |
| **Videojuegos** | *"Inicia el juego R.E.P.O."* o *"Abre PEAK"* | Lanza el juego a través del cliente de Steam |
| **Carpetas** | *"Abre la carpeta descargas"* | Inicia `explorer.exe` en la carpeta Downloads |
| **Archivos (Crear)** | *"Crea el archivo notas.txt con reunión a las 5"* | Escribe el archivo en disco |
| **Archivos (Borrar)**| *"Borra el archivo notas.txt"* | Elimina el archivo tras verificación |
| **Música** | *"Pon Queen en Spotify"* | Abre Spotify con la búsqueda activa |
| **Anime** | *"Busca anime Solo Leveling"* | Abre AnimeFLV / navegador con la serie |
| **Terminal** | *"Terminal ipconfig"* | Ejecuta el comando en PowerShell con logs en vivo |
| **Búsqueda Web** | *"Busca en Google noticias de tecnología"* | Abre consulta en el navegador predeterminado |
