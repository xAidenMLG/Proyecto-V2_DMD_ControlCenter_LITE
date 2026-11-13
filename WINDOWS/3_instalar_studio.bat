@echo off
REM ============================================================
REM  PASO 3 - Instalar DMD STUDIO (una sola vez; necesita internet)
REM  Crea el entorno virtual e instala fastapi + uvicorn
REM  (solo la capa web; los motores no necesitan nada).
REM ============================================================
call "%~dp0..\nucleo_engine_project\scripts\windows\install_studio.bat"
