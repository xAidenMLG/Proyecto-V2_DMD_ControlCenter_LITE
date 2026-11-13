# Informe de álbum — Ecos de Neblina

Generado: 2026-11-13T05:19:55 · esquema dmd-album-informe/1

**Pistas:** 3 · **OK:** 3 · **fallo:** 0 · **no ejecutadas:** 0 · **duración total:** 750.0 s (~12.5 min)

| # | Pista | Perfil | Seed | Armonía | Tonalidad | BPM | Comp. | Dur s | SHA256(16) | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | umbral_de_neblina | atmospheric | 9000 | — | F minor | 80 | 50 | 150.0 | 51bb6a6b8f3a11ec | ok |
| 2 | camara_de_espejos | full | 9101 | — | Bb minor | 80 | 100 | 300.0 | 511227d31a8ac2db | ok |
| 3 | marea_baja_de_neon | sax_rhodes | 9202 | — | F minor | 80 | 100 | 300.0 | 4b590b654666fba4 | ok |

## Diversidad y coherencia (métricas técnicas)

- Distribución de perfiles: {'atmospheric': 1, 'full': 1, 'sax_rhodes': 1}
- Exceso de perfil (> 40%): ninguno
- Consecutivas idénticas (perfil+tonalidad+BPM): ninguna
- Ventanas sin respiro: ninguna
- Duplicados exactos (SHA256): ninguno
- Similares sospechosos (Jaccard ≥ 0.85): ninguno
- Curva de energía objetivo: [0.45, 0.78, 0.15]
- Curva de energía real:    [0.494, 0.699, 0.229]
- Desviación máxima: 0.08
- Identidad del álbum: dark_triphop (consistente)
- Tonalidades: Bb minor, F minor
- BPM: 80 (referencia 76–92)

## Técnico vs musical

Medido automáticamente (técnico):

- duplicados exactos por SHA256 del MIDI
- similitud material por Jaccard de huellas (umbral 0.85)
- distribución y fracción de perfiles
- variedad en consecutivas (perfil+tonalidad+BPM)
- ventanas de respiro
- rango de BPM de referencia
- distancia tonal entre consecutivas
- adherencia a curva de energía
- compliance del validador de forge por pista

**Requiere escucha humana (pendiente de validación del usuario):**

- coherencia de identidad audible entre pistas
- fatiga de densidad o saturación de perfiles
- naturalidad de las transiciones entre pistas (orden de reproducción)
- calidad de las progresiones familiares activadas (si las hay)
- equilibrio sax/Rhodes/vibes/batería en el conjunto

## Reproducir

```bash
# álbum completo (regenera todo)
python3 -m album producir /home/z/my-project/nucleo_engine_project/albumes/ecos_de_neblina/album.json --out output/plan_f4/ecos_de_neblina --forzar

# una pista, verificada por hash
python3 scripts/produce.py output/plan_f4/ecos_de_neblina/01_umbral_de_neblina/doc.json --production atmospheric --seed 9000 --out output/plan_f4/ecos_de_neblina/01_umbral_de_neblina --verify 51bb6a6b8f3a11ecdc07ae9a214d49df4617b2d0ded14eebd7e70d0a3c6ce569
```

Manifiesto completo (config efectiva, hashes y comandos por pista): `manifiesto.json` · estado de ejecución: `estado.json`.
