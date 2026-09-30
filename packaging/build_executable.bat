@echo off
chcp 65001 > nul
echo =======================================================
echo 📦 COMPILADOR DE EJECUTABLE: VOCALOS DAEMON
echo Titular: Owen Badel Hooker
echo =======================================================

cd /d "%~dp0\.."

echo [1/2] Limpiando carpetas build y dist...
if exist "dist\VocalOS" rd /s /q "dist\VocalOS"
if exist "build\vocalos" rd /s /q "build\vocalos"

echo [2/2] Ejecutando PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "VocalOS" ^
    --add-data "data;data" ^
    --hidden-import "faster_whisper" ^
    --hidden-import "ctranslate2" ^
    --hidden-import "sounddevice" ^
    --hidden-import "scipy" ^
    --hidden-import "scipy.signal" ^
    --hidden-import "scipy.fft" ^
    --hidden-import "scipy.spatial.distance" ^
    --hidden-import "pystray" ^
    --hidden-import "PIL" ^
    vocalos_daemon.py

echo.
echo ✅ Compilación de PyInstaller finalizada.
echo Para generar el instalador final (.exe), compila 'packaging\VocalOS_Installer.iss' con Inno Setup Compiler.
pause
