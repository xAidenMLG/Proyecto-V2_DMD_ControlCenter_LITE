@echo off
REM ============================================================
REM  PASO 1 - Verificacion completa del proyecto en tu Windows
REM  Resultado esperado: 583 passed, 3 skipped, 71 subtests passed
REM  (~35 segundos). Los motores son 100 por ciento libreria
REM  estandar; pytest solo se usa para verificar.
REM ============================================================
setlocal
cd /d "%~dp0..\nucleo_engine_project"

echo [1/3] Comprobando Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo   ERROR: "python" no esta en el PATH. Instala Python 3.12.x de 64 bits
  echo   desde https://www.python.org/downloads/ marcando "Add python.exe to PATH".
  pause & exit /b 1
)
python --version

echo.
echo [2/3] Comprobando pytest (solo para la verificacion)...
python -m pytest --version >nul 2>&1
if errorlevel 1 (
  echo   pytest no esta instalado; instalando (internet solo esta vez)...
  python -m pip install pytest --quiet
  if errorlevel 1 (
    echo   ERROR instalando pytest. Alternativa manual:
    echo     python -m pip install pytest
    pause & exit /b 1
  )
)

echo.
echo [3/3] Ejecutando la suite completa (586 tests)...
python -m pytest tests -q
echo.
echo Resultado esperado: 583 passed, 3 skipped, 71 subtests passed
pause
