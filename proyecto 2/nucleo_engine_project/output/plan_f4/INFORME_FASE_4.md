# INFORME FASE 4 — Album Blueprint MVP (DMD Control Center)

Fecha de cierre: 2026-11-13 · Spec de referencia: DMD Control Center v1.4 (§8, §12.1 Fase 4)
Baseline: tag `cc-f3-ok` (commit `acb628d`, estado F3 cerrada) · Base de trabajo: `5c9520e` (post-reparación A1)
Modo de trabajo: autorización general del usuario («todo queda abierto… misión de toma de decisiones hasta que el proyecto total esté completado», 2026-11-13) — se ejecutó la fase con el régimen de evidencia intacto.

---

## 1. Resumen ejecutivo

F4 implementa el **Album Blueprint MVP**: el nivel álbum del sistema, montado sobre los dos
subsistemas existentes y cerrados. Un único módulo nuevo (`album/blueprint.py`) toma un
**bloque de identidad global** (§8.1: receta, protagonista, paleta de perfiles, vocabulario
armónico) más **deltas por pista** (arco de energía, duración, drums, variación del
protagonista) y **deriva el álbum ejecutable completo** por la ruta REAL de Fase 2
(intérprete → capas A/B → compilador → doc dark-director/1), que entrega al pipeline REAL de
FASE 8 (`album.json` → `python3 -m album producir` → MIDIs deterministas + huellas + informe).

Implementado y verificado: álbum dorado **«Ecos de Neblina»** (3 pistas) producido de punta a
punta con el motor real; **reglas de álbum §8.4 en 4/4 (+ P-03)**; diversidad en banda (peor
par Jaccard 0.2746 vs umbral de monotonía 0.85; referencia del álbum previo: máx 0.399);
**P-03 CERRADO por la vía (a) del contrato** — el motivo firma se escribe una vez en el
blueprint, viaja transpuesto a la tonalidad de cada pista por `development.melody.phrases` +
`development.motifs` (mecanismo consumido hoy por el validador y el compilador dark-director)
y está **probado en el MIDI real por eventos exactos** (recurrencia verse→chorus en las
pistas 1–2, ausencia en la 3); determinismo byte a byte (derivación y re-producción
`--forzar` idénticas); **suite completa del proyecto: 571 passed** (526 de F3 + 45 nuevos de
F4), 0 fallos.

Gate de avance de la fase (§12.1): **reglas 4/4 ✓ · diversidad en banda ✓ · escucha comparada
≥ banda → PENDIENTE (Capa D del usuario; protocolo entregado)**.

## 2. Alcance y archivos

**Código nuevo (único archivo de código de la fase):**
- `album/blueprint.py` (~740 líneas): schema `dmd-album-blueprint/1` + derivación + reglas §8.4 + banda de huellas + CLI (`python3 -m album.blueprint`).

**Ningún archivo existente fue modificado.** El hook de integración que el spec autorizaba
(«si `orquestador.py` no expone API suficiente») **no hizo falta**: `orquestador.ejecutar()`
cubre la integración tal cual — el blueprint genera `album.json` + `docs/` y el pipeline
existente produce el resto. Queda registrado aquí como exige el spec §12.1.

**Tests nuevos:** `tests/fase4/` (37 unit + 8 golden; convención `tests/faseN` del repo).

**Artefactos:** `albumes/ecos_de_neblina/` (blueprint.json fuente + album.json + docs/ +
resolución) y `output/plan_f4/ecos_de_neblina/` (producción: plan.json, estado.json,
huellas.json, informe_album.md/.json, manifiesto.json, 3 pistas con MIDI).

## 3. Arquitectura del blueprint

```
blueprint.json (dmd-album-blueprint/1)
  │  identidad global §8.1 + arco de deltas §8.1 + motivo firma (P-03)
  ▼
album/blueprint.py
  ├─ por pista: intención {identidad global + delta} ──► control_center.interprete.resolver()
  │                                            └──────► validador (capas A/B) — fail-fast
  ├─ tonalidad por pista: pool de la tónica ±1 alteración (RA4 por construcción;
  │   círculo de quintas REUTILIZADO de validador._FIFTHS_MENOR — cero duplicación)
  ├─ solo de rol_acompanante: materialización Advanced solos[] (§9.2) sobre el
  │   break/bridge de mayor energía del esqueleto ya resuelto
  ├─ motivo firma: development.melody.phrases + development.motifs en el doc
  │   (vía (a) del contrato; transposición por pista con búsqueda de octava
  │   para respetar el registro del lead 62–81; ausente en ≥1 pista)
  └─ album.json (dmd-album/1) + docs/NN_<id>.json + blueprint_resolucion.json
        ▼
python3 -m album producir   (pipeline FASE 8 REAL: planificador → orquestador →
                             producir_cancion → huellas → informe)
```

Decisiones de diseño documentadas:

1. **Sin hook en `orquestador.py`.** La API existente bastó (§12.1 exige dejarlo por escrito).
2. **`album_context` sigue siendo null en las intenciones.** La coherencia de álbum vive en el
   blueprint (pool de tonalidades declarado concreto por pista vía `harmony.key`, que el
   intérprete respeta — paso 3 verificado), no en un campo nuevo del plan: el plan v1 queda
   intacto y los tests de F1/F2 no se tocan.
3. **Perfiles explícitos en el álbum derivado.** El perfil de cada pista es el que el
   intérprete resolvió (R23: drums + energía dentro de la paleta), declarado en el álbum para
   que la producción use EXACTAMENTE lo validado por capas A/B.
4. **Seeds por la fórmula del planificador** (`seed = semilla_album + 101·índice`,
   documentada en ambos módulos) — reproducibilidad alineada con FASE 8.

## 4. Mapeo de las variaciones del protagonista (§8.1 → vocabulario real)

| Delta declarado | Traducción real (intérprete F2) | Evidencia |
|---|---|---|
| `mismo` | protagonista global; sin overrides | plan sin solos; V113 garantiza focus ≥2 secciones |
| `registro_distinto` | protagonista melódico alterno (rotación determinista sax_tenor→vibraphone→rhodes→sax_tenor); con energía ≥ alta el intérprete añade su solo automático (R22) | pista 2: protagonista vibraphone, solo automático en `bridge_6` |
| `rol_acompanante` | el protagonista acompaña: solo declarado de OTRO melódico vía `solos[]` (ruta Advanced §9.2) sobre el break/bridge de mayor energía; el intérprete lo materializa (type break + focus) | pista 3: solo de rhodes en `bridge_6`; sax acompaña (statement de sección) |

R30 respetado: ningún solo automático del lead sax (el blueprint no declara solos de
sax_tenor; el solo de la pista 3 es de rhodes, materializado por focus — sin gate C4s).

## 5. P-03 — decisión de la fase: motivo firma por la vía (a) del contrato

**Decisión: P-03 CIERRA con la vía (a).** La frase firma se escribe UNA VEZ en el blueprint
(`motivo_firma.frase`, notas del contrato {bar, beat, pitch, dur, vel}) y se propaga a los
docs de las pistas que la referencian por el mecanismo que el contrato ya consume hoy:
`development.melody.phrases` (fuente) + `development.motifs` (recurrencia intra-pista,
§2.7.1 del compilador dark-director). La vía (b) (consumidor nuevo de `x_*`) queda
descartada, como anticipaba el spec: transportar metadata no es ejecutar una decisión
musical.

Propiedades verificadas con evidencia real:

1. **Transposición por tonalidad.** La frase viaja al pool de la pista con búsqueda de
   octava que respeta el registro del lead (62–81): pista 1 en F minor (65, 68, 72, 70, 67),
   pista 2 en Bb minor (+5 st: 70, 73, 77, 75, 72).
2. **Recurrencia intra-pista.** `motifs.firma_neblina: verse_2 → chorus_4 (pista 1) /
   chorus_8 (pista 2)`, `transpose_st: 0` (la frase ya viaja transpuesta al doc).
3. **Presencia en el MIDI real (eventos exactos).** Pista 1: el sax toca
   `65→68→72→70→67` en verse_2 (beats 32–46) y **la misma secuencia exacta** en chorus_4
   (beats 108–122). Pista 2: `70→73→77→75→72` en verse_2 y **recurrencia idéntica** en
   chorus_8 (beats 312–326). Evidencia: events.json regenerado con `produce.py --events`
   (tests `test_motivo_firma_en_el_midi_real`, `test_eventos_reales_del_lead`).
4. **Anti-monotonía (mitigación del §12.1).** La ÚLTIMA pista del álbum no lleva motivo
   (regla P-03: presente ≥1 y ausente ≥1). La pista de contraste («Marea Baja de Neón»)
   respira sin la firma.
5. **E204 respetado por construcción.** El material escrito se coloca solo en secciones con
   el lead en focus (`verse/pre_chorus/chorus` del plan resuelto) — y el criterio contractual
   `suena(sax_tenor)` es válido en todas las secciones del intérprete.
6. **Compliance warn `motif_repeat` (caracterizado, no bloqueante).** El check de
   `forge/validate.py` (bucles de 8 compases con ritmo idéntico DENTRO de cada coro) emite
   warn en las 3 pistas: la heurística busca repetición de bucle intra-coro (caso
   nochechocho `loop_bars=8`); nuestro motivo recurre cross-sección una vez por coro, así
   que los bucles del coro no comparten firma rítmica exacta. La recurrencia REAL está
   demostrada por eventos exactos (punto 3). Registrado en `evidencia.json` como
   `compliance_warns: ['motif_repeat']` — 0 fails.

## 6. El álbum dorado — «Ecos de Neblina»

Universo dark_triphop · tónica F minor · pool {F, Bb, C minor} · pulso swing (80 BPM) ·
carácter nocturno (pop_dream_pop) · semilla_album 8899.

| # | Pista | Arco | Tonalidad | Perfil (R23) | Seed | Variación | Solo | Compases | Dur | SHA256 MIDI (16) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Umbral de Neblina | 0.45 | F minor | atmospheric | 9000 | mismo | — | 50 | 150 s | 51bb6a6b8f3a11ec |
| 2 | Cámara de Espejos | 0.78 | Bb minor | full | 9101 | registro_distinto | vibraphone (auto R22) | 100 | 300 s | 511227d31a8ac2db |
| 3 | Marea Baja de Neón | 0.15 | F minor | sax_rhodes | 9202 | rol_acompanante | rhodes (Advanced §9.2) | 100 | 300 s | 4b590b654666fba4 |

Arco: apertura media → clímax alto → cierre muy bajo (12.5 min totales). El motivo firma
abre en la 1, refleja transpuesto en la 2 y descansa en la 3.

**Reglas §8.4 — 4/4 (+ P-03):**

| Regla | Resultado | Detalle medido |
|---|---|---|
| RA1 pista de contraste (< 0.35) | PASS | arco 0.15; energía real 0.229 |
| RA2 ≤2 consecutivas mismo perfil | PASS | racha máxima 1 (atmospheric → full → sax_rhodes) |
| RA3 solos no consecutivos | PASS | secuencia — → vibraphone → rhodes |
| RA4 identidad + tónicas ≤1 alteración | PASS | dark_triphop 3/3; F↔Bb: 1; Bb↔F: 1 |
| P-03 motivo presente/ausente | PASS | con: pistas 1–2; sin: pista 3 |

**Diversidad POST (huellas Jaccard):** peor par 0.2746 (umbral de monotonía 0.85; el álbum
previo `noches_largas` alcanzó 0.399) — en banda, sin duplicados exactos.

**Curva de energía:** objetivo [0.45, 0.78, 0.15] vs real [0.494, 0.699, 0.229] — desviación
máxima 0.08 (tolerancia W-A8: 0.15). El planificador se ejecutó en seco sin UN SOLO aviso.

## 7. Pruebas y verificación

- `tests/fase4/test_fase4_blueprint.py` — 37 unit: fail-fast del schema (10 casos B-código),
  pool armónico (reutilización de la tabla de la capa A), bandas de energía, determinismo de
  derivación byte a byte (incluye comparación contra el dorado en disco), reglas §8.4, motivo
  (orden del doc = orden de produce.py, frase, transposición, ausencia, compilación en el
  contrato real, registro del lead), variaciones (incluye slot break/bridge materializado),
  integración con el planificador real (dry-run sin avisos graves).
- `tests/fase4/test_fase4_golden.py` — 8 golden de producción sobre disco real: producción
  exitosa 3/3 con 0 compliance fails, artefactos completos por pista, informe+manifiesto,
  banda de diversidad sin duplicados, reglas 4/4, motivo en el MIDI real (docs + eventos del
  lead con recurrencia), determinismo de re-producción `--forzar` (sha256 idénticos).
- **Suite completa del proyecto: 571 passed, 3 skipped, 71 subtests — 0 fallos**
  (F3 cerraba con 526+3; los 45 nuevos son exactamente los de F4).
- Hallazgo de los propios tests: la primera tabla del círculo de quintas del blueprint tenía
  el lado de bemoles desplazado (Eb minor entraba al pool de F minor a 2 alteraciones —
  violaría RA4). Corregido reutilizando `_FIFTHS_MENOR` de la capa A (cero duplicación).

## 8. Límites honestos (lo que el MVP NO promete — §8.2)

- **Narrativa**: las pistas comparten casa, no historia semántica (C-03 sigue pospuesta).
- **Coherencia motívica**: PROMETIDA y entregada como contorno transpuesto + recurrencia
  intra-pista; NO como desarrollo temático largo entre pistas.
- **La escucha comparada** (tercer gate de la fase) es Capa D: no automatizable; protocolo
  entregado en `PROTOCOLO_ESCUCHA_F4.md`, veredicto pendiente del usuario.
- El MVP no promete el retorno del motivo en TODAS las pistas: por diseño falta en ≥1
  (anti-monotonía del §12.1 — `diversidad.py` manda).

## 9. Rollback y reversibilidad

Todo lo nuevo de la fase es aditivo: borrar `album/blueprint.py`, `tests/fase4/`,
`albumes/ecos_de_neblina/` y `output/plan_f4/` restaura exactamente el estado de `cc-f3-ok`
(nada existente fue modificado; verificado con `git diff`). Disparadores de rollback del
spec: monotonía fuera de banda (no ocurrió: 0.2746 < 0.85) o reglas incumplidas persistentes
(no ocurrió: 4/4 + P-03 al primer gate completo).

## 10. Conclusión

F4 queda **cerrada técnicamente dentro del alcance del spec**: Album Blueprint MVP operando
de punta a punta sobre las autoridades intactas (produce.py, dark_director, jazz_engine,
forge — verificado con el diff de la fase: solo archivos nuevos), reglas de álbum 4/4,
diversidad en banda, P-03 cerrado con mecanismo real y evidencia musical en el MIDI. El gate
de Capa D (escucha comparada de las 3 pistas) queda listo para el usuario con protocolo y
comandos de reproducción exactos. F5 (Endurecimiento y verificación) continúa a continuación
dentro de la misma autorización.

**Pendiente de la fase:** único ítem abierto = veredicto de escucha comparada (Capa D).
