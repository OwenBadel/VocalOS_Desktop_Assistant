@echo off
rem ========================================================
rem Ari - Asistente de Escritorio en Espanol
rem Autor: Owen Badel Hooker
rem ========================================================
setlocal

cd /d "%~dp0"

echo [Ari] Iniciando Asistente de Escritorio...
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" run_ari.py
) else (
    python run_ari.py
)

if errorlevel 1 (
    echo.
    echo [Error] La aplicacion se cerro con error.
    pause
)

endlocal
