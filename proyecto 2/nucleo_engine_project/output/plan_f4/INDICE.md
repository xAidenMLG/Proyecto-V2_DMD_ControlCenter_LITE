# Índice — output/plan_f4 (Fase 4: Album Blueprint MVP)

| Archivo/carpeta | Contenido |
|---|---|
| `INFORME_FASE_4.md` | Informe final autocontenido de la fase (gate, arquitectura, decisiones P-03, tests, evidencia, límites honestos) |
| `PROTOCOLO_ESCUCHA_F4.md` | Protocolo de escucha comparada de las 3 pistas del álbum dorado (gate de Capa D pendiente del usuario) |
| `ecos_de_neblina/` | Producción real del álbum dorado: `plan.json`, `estado.json`, `huellas.json`, `informe_album.md/.json`, `manifiesto.json` y las 3 pistas (`NN_<id>/` con doc.json, config_efectiva.json, evidencia.json, MIDI) |

Fuente creativa y código:

| Ruta | Contenido |
|---|---|
| `albumes/ecos_de_neblina/blueprint.json` | Blueprint dorado (schema `dmd-album-blueprint/1`): identidad global + arco de 3 deltas + motivo firma «firma_neblina» |
| `albumes/ecos_de_neblina/album.json` | Álbum derivado (schema `dmd-album/1`) — byte-determinista desde el blueprint |
| `albumes/ecos_de_neblina/docs/` | Los 3 docs dark-director/1 derivados por la ruta real F2 (con `development.*` inyectado por contrato) |
| `albumes/ecos_de_neblina/blueprint_resolucion.json` | Evidencia de derivación: seeds, tonalidades, perfiles, solos, motivo, hashes |
| `album/blueprint.py` | Módulo nuevo de la fase (único archivo de código): blueprint → ruta real F2 → pipeline real FASE 8 + reglas §8.4 |
| `tests/fase4/test_fase4_blueprint.py` | 37 tests unitarios (esquema, pool armónico, determinismo, reglas, motivo, variaciones) |
| `tests/fase4/test_fase4_golden.py` | 8 tests golden de producción (gate F4 completo sobre disco real) |

Estado de la fase: **FASE 4 CERRADA TÉCNICAMENTE** — gate automatizado completo (reglas §8.4 4/4 + P-03,
diversidad en banda, determinismo byte a byte, suite completa 571 verdes). Pendiente ÚNICO: Capa D de
escucha comparada del álbum (protocolo listo; corresponde al usuario).
