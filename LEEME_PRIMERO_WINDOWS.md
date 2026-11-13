# LEEME PRIMERO — DMD Control Center · paquete LITE (solo el programa)

Fecha del paquete: 2026-11-13 · Spec: DMD Control Center v1.4 · Estado: **roadmap F1–F5
COMPLETADO** · Veredicto de escucha humana (Capa D) registrado: **«totalmente aceptados
los midis»** (actas `APROBACION_CAPA_D.md` en `nucleo_engine_project\output\plan_f4\` y
`nucleo_engine_project\output\plan_f5\`).

## Qué es este paquete LITE

El MISMO programa que el paquete completo, sin la basura:

- Sin historia `.git` (la evidencia de integridad aquí son las actas con SHA256 y
  `nucleo_engine_project\manifests\`).
- Sin copias históricas (`staging\`, `nucleo_engine_project_light\`, `DMD_Composer\`).
- Sin el espejo `download\` (las mismas entregas ya viven en `nucleo_engine_project\output\`).
- Sin cachés `__pycache__`, sin pruebas temporales (`dmd_tests_tmp`), sin respaldos
  de fases (`backups`) y sin el registro de jobs del Studio (`studio_data\jobs\`
  se recrea vacío la primera vez que uses el Studio).

Nada del programa cambió: mismos motores, mismos tests, mismos MIDIs aprobados
(mismos SHA256 que el acta). El paso 1 de calado da el mismo resultado:
`583 passed, 3 skipped, 71 subtests passed`.

## 1. Requisitos

| Para qué | Qué necesitas | Notas |
|---|---|---|
| Motores (dark_director, jazz_engine, forge, produce.py, album) | Solo **Python 3.8+** (recomendado 3.12.x de 64 bits) | 100 % librería estándar: sin `pip install`, sin internet |
| Verificación de la suite (paso 1) | Python + **pytest** | El bat lo instala solo la primera vez (una línea, requiere internet solo entonces) |
| DMD Studio, app web local (pasos 3–4) | Python + `fastapi`+`uvicorn` | El bat `3_instalar_studio.bat` crea el venv e instala (requiere internet, una vez) |

Instala Python desde https://www.python.org/downloads/ marcando la casilla
**«Add python.exe to PATH»** (sin eso ningún bat funcionará).

Consejo: descomprime el zip en una carpeta **corta**, p. ej. `C:\DMD\`.

## 2. Los 4 pasos de calado (carpeta `WINDOWS\`)

| Paso | Bat | Qué prueba | Resultado esperado |
|---|---|---|---|
| 1 | `1_verificar_tests.bat` | Suite completa del proyecto | `583 passed, 3 skipped, 71 subtests passed` (~35 s) |
| 2 | `2_producir_album.bat` | Producción real del álbum + determinismo en TU máquina | Los 3 SHA256 coinciden con el acta (tabla abajo) |
| 3 | `3_instalar_studio.bat` | Instalación del Studio (una vez) | «Instalacion completada» |
| 4 | `4_iniciar_studio.bat` | La app: http://127.0.0.1:8899 | El Studio abre en tu navegador |

Doble clic en cada bat (o ejecútalos desde `cmd`). El paso 2 produce en
`nucleo_engine_project\output\prueba_windows\ecos_de_neblina\` — un directorio NUEVO,
no toca ninguna entrega existente.

## 3. Determinismo: hashes de referencia (acta `APROBACION_CAPA_D.md`)

Mismo blueprint ⇒ mismos MIDIs, byte a byte, en cualquier máquina. Tras el paso 2,
compara con `certutil -hashfile <archivo.mid> SHA256` (los primeros 16 caracteres):

| Pieza | Perfil | Seed | SHA256 (primeros 16) |
|---|---|---|---|
| 01_umbral_de_neblina.mid | atmospheric | 9000 | `51bb6a6b8f3a11ec` |
| 02_camara_de_espejos.mid | full | 9101 | `511227d31a8ac2db` |
| 03_marea_baja_de_neon.mid | sax_rhodes (sin drums) | 9202 | `4b590b654666fba4` |

El bat del paso 2 hace esto por ti y muestra la referencia al final.

## 4. Dónde están los MIDIs aprobados (en este paquete)

| Conjunto | Carpeta |
|---|---|
| Álbum «Ecos de Neblina» (3 pistas, acta plan_f4) | `nucleo_engine_project\output\plan_f4\ecos_de_neblina\` |
| Serie base MVP sin seed (5 piezas, acta plan_f5) | `nucleo_engine_project\output\plan_f5\serie_base\` |
| Comparativos F5 (8 variantes con GOLDEN.md) | `nucleo_engine_project\output\fase5_comparativos\` |
| Generalización F6 + paquete auditivo | `nucleo_engine_project\output\generalizacion_fase6\` y `output\fase6_paquete_auditivo\` |
| Comparativos F7 (A/B/C/D por pieza) | `nucleo_engine_project\output\fase7_comparativos\` |
| Producción y experimentos | `nucleo_engine_project\output\produccion\` y `output\experimentos\` |
| Actas de aprobación Capa D | `output\plan_f4\APROBACION_CAPA_D.md` y `output\plan_f5\APROBACION_CAPA_D.md` |

## 5. Cómo escuchar los MIDIs en tu Windows

1. **Studio (recomendado)**: pasos 3–4 → el reproductor de vista previa del navegador
   suena con sintetizador WebAudio, sin instalar nada.
2. **Audio con instrumentos reales (opcional)**: instala FluidSynth (`fluidsynth.exe`
   en el PATH o en `tools\`) y un soundfont `.sf2` en `soundfonts\` — flujo documentado
   en `nucleo_engine_project\README.md` (sección WAV).
3. **Cualquier DAW** (Reaper, FL Studio, Cubase…) abre los `.mid` directamente.
   Nota: Windows 10/11 ya no trae sintetizador MIDI integrado en el reproductor,
   por eso se recomienda 1 o 3.

## 6. Mapa del contenido (LITE)

| Carpeta | Qué es |
|---|---|
| `nucleo_engine_project\` | **El proyecto vivo completo**: motores (`dark_director`, `jazz_engine`, `forge`, `scripts\produce.py`), Control Center, álbum, Studio + web, tests (la misma suite), docs y outputs aprobados |
| `WINDOWS\` | Los 4 bats de calado (idénticos al paquete completo) |
| `LEEME_PRIMERO_WINDOWS.md` | Este documento |

## 7. Problemas frecuentes

- **`python no esta en el PATH`** → reinstala Python marcando «Add python.exe to PATH».
- **pytest falta y no hay internet** → los motores y el paso 2 funcionan igual; solo el
  paso 1 lo necesita (o instala pytest donde tengas internet: `python -m pip install pytest`).
- **Windows bloquea el bat** («Windows protegió tu PC») → «Más información» →
  «Ejecutar de todas formas»; son scripts locales legibles.
- **Rutas largas al descomprimir** → usa `C:\DMD` o 7-Zip.
- **El Studio no abre** → mira la consola del paso 4: si falta el venv, corre antes el
  paso 3; el servidor solo escucha en 127.0.0.1 (nada sale a internet).
