@echo off
REM ============================================================
REM  PASO 2 - Regenerar el album "Ecos de Neblina" (determinismo)
REM  Produce los 3 MIDIs en un directorio NUEVO
REM  (nucleo_engine_project\output\prueba_windows\ecos_de_neblina)
REM  sin tocar ninguna entrega existente.
REM  Esperado: mismos SHA256 que el acta (se muestran al final).
REM ============================================================
setlocal
cd /d "%~dp0..\nucleo_engine_project"

python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: "python" no esta en el PATH. Ver LEEME_PRIMERO_WINDOWS.md
  pause & exit /b 1
)

echo Produciendo el album con el pipeline real...
python -m album producir albumes/ecos_de_neblina/album.json --out output\prueba_windows\ecos_de_neblina
if errorlevel 1 (
  echo ERROR en la produccion
  pause & exit /b 1
)

echo.
echo SHA256 de los MIDIs regenerados:
for %%F in (output\prueba_windows\ecos_de_neblina\0*\*.mid) do call :hash "%%F"
echo.
echo Referencia del acta (deben coincidir los primeros 16 caracteres):
echo   01_umbral_de_neblina.mid  = 51bb6a6b8f3a11ec
echo   02_camara_de_espejos.mid  = 511227d31a8ac2db
echo   03_marea_baja_de_neon.mid = 4b590b654666fba4
echo.
echo Si coinciden: determinismo byte a byte confirmado en tu maquina.
pause & exit /b 0

:hash
for /f "delims=" %%H in ('certutil -hashfile %1 SHA256 ^| findstr /r "^[0-9a-f]"') do (
  echo   %~nx1 = %%H
)
goto :eof
